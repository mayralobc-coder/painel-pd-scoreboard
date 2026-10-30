import unicodedata

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="P&D por país", layout="wide")
st.title("P&D por país (2003–2024)")

# Símbolo da moeda. O Scoreboard da Comissão Europeia vem em milhões de euros.
# Se o professor disser que a tabela foi convertida para dólar, troque por "US$".
MOEDA = "€"

# nome que aparece no painel -> nome da aba no Excel
ABAS = {
    "Gasto em P&D": "R&D",
    "Receitas": "Sales",
    "Investimento (Capex)": "Capex",
    "Empregos": "Emprego",
    "Capitalização": "Capitaliza",
    "Número de empresas": "Empesas",
}

# métricas que são dinheiro (as outras são contagens)
EM_DINHEIRO = ["Gasto em P&D", "Receitas", "Investimento (Capex)", "Capitalização"]

# nome do país na base (inglês) -> nome em português
NOMES = {
    "US": "EUA", "China": "China", "Japan": "Japão", "Germany": "Alemanha",
    "France": "França", "UK": "Reino Unido", "South Korea": "Coreia do Sul",
    "Taiwan": "Taiwan", "India": "Índia", "Brazil": "Brasil",
    "Switzerland": "Suíça", "Netherlands": "Países Baixos", "Sweden": "Suécia",
    "Canada": "Canadá", "Italy": "Itália", "Singapore": "Singapura",
    "Spain": "Espanha", "Australia": "Austrália", "Austria": "Áustria",
    "Belgium": "Bélgica", "Denmark": "Dinamarca", "Finland": "Finlândia",
    "Ireland": "Irlanda", "Israel": "Israel", "Norway": "Noruega",
    "Russia": "Rússia", "Mexico": "México", "Argentina": "Argentina",
    "Hong Kong": "Hong Kong", "Luxembourg": "Luxemburgo",
    "Saudi Arabia": "Arábia Saudita", "Türkiye": "Turquia",
    "South Africa": "África do Sul",
    "United Arab Emirates": "Emirados Árabes Unidos", "Poland": "Polônia",
    "Portugal": "Portugal", "Greece": "Grécia", "Cayman Islands": "Ilhas Cayman",
    "Colombia": "Colômbia", "Cyprus": "Chipre", "Czechia": "Tchéquia",
    "Hungary": "Hungria", "Iceland": "Islândia", "Indonesia": "Indonésia",
    "Iraq": "Iraque", "Liechtenstein": "Liechtenstein", "Malaysia": "Malásia",
    "Malta": "Malta", "New Zealand": "Nova Zelândia", "Romania": "Romênia",
    "Slovenia": "Eslovênia", "Thailand": "Tailândia", "Ukraine": "Ucrânia",
    "Venezuela": "Venezuela", "Vietnam": "Vietnã",
}


def carregar(aba):
    """Lê uma aba e devolve a tabela com anos nas linhas e países nas colunas."""
    df = pd.read_excel("Dados.xlsx", sheet_name=aba)
    df = df.set_index("Rótulos de Linha")
    df = df.drop(columns=["(vazio)", "Total Geral"])
    return df.T


def numero_br(valor, simbolo=""):
    """1234567.8 vira '€ 1.234.568' (milhar com ponto, como no Brasil)."""
    return simbolo + f"{valor:,.0f}".replace(",", ".")


def pct_br(valor):
    """45.93 vira '45,9%' (vírgula decimal, como no Brasil)."""
    return f"{valor:.1f}".replace(".", ",") + "%"


def para_ordenar(pais):
    """Nome em português sem acento, para a lista ficar em ordem alfabética."""
    nome = NOMES.get(pais, pais)
    return unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()


# ---- filtros na barra lateral ----
metrica = st.sidebar.selectbox("Métrica", list(ABAS))
modo = st.sidebar.radio(
    "Visualização", ["Valor absoluto", "Participação no total mundial (%)"]
)

tabela = carregar(ABAS[metrica])

# lista de países do filtro: tudo, menos o total e o "(vazio)"
opcoes = [p for p in tabela.columns if p not in ["Total Geral", "(vazio)"]]
opcoes = sorted(opcoes, key=para_ordenar)

paises = st.sidebar.multiselect(
    "Países", opcoes, default=["US", "China"], format_func=lambda p: NOMES.get(p, p)
)
if not paises:
    st.warning("Escolha pelo menos um país na barra lateral.")
    st.stop()

# Erro na base: a Colômbia aparece com receita de ~50 milhões em 2015
# (em 2014 eram ~21 mil e em 2016 ~10 mil). Tiramos esse valor do total mundial.
if ABAS[metrica] == "Sales":
    tabela.loc[2015, "Total Geral"] = (
        tabela.loc[2015, "Total Geral"] - tabela.loc[2015, "Colombia"]
    )

# ---- escolhe o que mostrar ----
if modo == "Valor absoluto":
    resultado = tabela[paises]
else:
    resultado = tabela[paises].div(tabela["Total Geral"], axis=0) * 100

resultado = resultado.rename(columns=NOMES)

# avisa se algum país escolhido não tem dados nesta métrica
sem_dados = resultado.columns[resultado.isna().all()]
if len(sem_dados) > 0:
    st.warning("Sem dados nesta métrica: " + ", ".join(sem_dados))

# símbolo da moeda só aparece em valor absoluto de métricas em dinheiro
simbolo = ""
if modo == "Valor absoluto" and metrica in EM_DINHEIRO:
    simbolo = MOEDA + " "

# texto do eixo vertical (a unidade)
if modo != "Valor absoluto":
    rotulo_y = "% do total mundial"
elif metrica in EM_DINHEIRO:
    rotulo_y = f"Milhões de {MOEDA}"
elif metrica == "Empregos":
    rotulo_y = "Pessoas empregadas"
else:
    rotulo_y = "Número de empresas"

# ---- gráfico ----
fig = px.line(resultado, markers=True, title=f"{metrica}: {modo}")
fig.update_layout(
    xaxis_title="Ano", yaxis_title=rotulo_y, legend_title="País", separators=",."
)
if modo == "Valor absoluto":
    fig.update_yaxes(tickprefix=simbolo, tickformat=",.0f")
    fig.update_traces(hovertemplate="%{x}: " + simbolo + "%{y:,.0f}")
else:
    fig.update_yaxes(ticksuffix="%")
    fig.update_traces(hovertemplate="%{x}: %{y:.1f}%")
st.plotly_chart(fig)

# ---- tabela ----
if modo == "Valor absoluto":
    tabela_final = resultado.style.format(lambda v: numero_br(v, simbolo), na_rep="–")
else:
    tabela_final = resultado.style.format(pct_br, na_rep="–")
st.dataframe(tabela_final)


# ================== ANÁLISE ==================
st.divider()
st.header("Análise dos resultados")
st.caption(
    "Rascunho para revisar e reescrever com suas palavras. Os números foram "
    "calculados a partir do Dados.xlsx (valores em milhões de euros)."
)

with st.expander("1. EUA x China: quem lidera?", expanded=True):
    st.markdown(
        """
- **P&D:** a participação dos EUA no total da base passou de 41,5% (2005) para
  45,9% (2024). A da China foi de 0,7% para 16,0%. Em 2005 o P&D chinês
  equivalia a 2% do americano; em 2024, a 35%.
- **Onde a China já alcançou os EUA, nas empresas da base:** em **empregos** (a
  partir de 2015; em 2024 tem 1,28 vez o nível americano) e em **Capex** (a
  partir de 2020, mas em 2024 voltou a 72% do nível dos EUA). Em P&D, número de
  empresas, receitas e capitalização, ainda não passou. Atenção: isso vale para
  as empresas da base, em euros. Pelas estatísticas nacionais da OCDE, a China
  já superou os EUA em P&D total em 2024 (veja as caixas 4 e 5).
- **Tamanho relativo em 2024 (China ÷ EUA):** P&D 0,35; empresas 0,80;
  receitas 0,77; Capex 0,72; capitalização 0,13.
- **Capitalização:** os EUA subiram de 39,9% para 58,4% do total e a China de
  2,7% para 7,4%. Em 2024, a fatia americana na capitalização (58,4%) é bem
  maior que no P&D (45,9%), e a chinesa (7,4%) é bem menor que no P&D (16,0%).
"""
    )

with st.expander("2. Esforço de inovação: intensidade e tamanho médio"):
    st.markdown(
        """
- **Intensidade de P&D (P&D ÷ receitas), 2005 → 2024:** EUA de 4,3% para 8,8%;
  China de 0,7% para 4,0%; total da base de 3,1% para 5,1%. As empresas dos dois
  países aumentaram o esforço, mas as americanas seguem com mais que o dobro da
  intensidade das chinesas.
- **P&D médio por empresa:** EUA de 299 para 1.007 milhões de euros; China de 28
  para 437 milhões de euros.
- A diferença de intensidade pode refletir o perfil setorial de cada país
  (hipótese a testar com a aba Setores).
"""
    )

with st.expander("3. Atenção ao ano de 2024"):
    st.markdown(
        """
- Em 2024 o P&D dos EUA cresceu 19,3%, contra 5,9% do total da base e 3,2% da
  China. No ano anterior (2022 → 2023), os EUA tinham crescido 2,8%.
- O número de empresas na base cai: 3.057 (2022), 2.493 (2023) e 2.407 (2024).
  Nos EUA, de 861 para 666; na China, de 707 para 535. Assim, o P&D médio por
  empresa americana vai de 636 milhões (2022) para 1.007 milhões (2024).
- Isso pode refletir mudança na cobertura da base, e não só crescimento real.
  Antes de concluir que "os EUA aceleraram", vale confirmar com o professor
  como a base foi montada nos últimos anos.
- Um contraponto vem da China: segundo o NBS (via Monitor Mercantil), o gasto
  total do país em P&D cresceu em média 10% ao ano entre 2021 e 2025. Na base,
  o P&D das empresas chinesas cresceu cerca de 6,4% ao ano entre 2021 e 2024
  (em euros), e a participação da China parou de subir em 2022. Como o número
  de empresas chinesas na base caiu de 738 para 535 nesse período, a
  estagnação pode vir da cobertura da base (ou do câmbio) e não de uma
  desaceleração real. É uma hipótese a confirmar.
"""
    )

with st.expander("4. O que dizem as fontes"):
    st.markdown(
        """
- **[Carta IEDI n. 1317](https://www.iedi.org.br/cartas/carta_iedi_n_1317.html)
  (18/06/2025):** a China é o segundo maior investidor em P&D do mundo, atrás
  dos EUA. O gasto em P&D (GERD) passou de 0,57% do PIB em 1995 para 2,3% em
  2020. Cerca de 85% vai para desenvolvimento experimental ligado à produção,
  10% para pesquisa aplicada e 5% para pesquisa básica. A carta destaca os
  parques tecnológicos como peça da política industrial chinesa.
- **[NSF 25-353](https://ncses.nsf.gov/pubs/nsf25353):** as empresas realizaram
  722 bilhões de dólares (valores correntes) de P&D nos EUA em 2023, alta de 4,4%
  sobre 2022. Desse total, 79% foi desenvolvimento, 15% pesquisa aplicada e 6%
  pesquisa básica, e 55% foi feito pela indústria de transformação.
- **[Monitor Mercantil](https://monitormercantil.com.br/investimento-da-china-em-pd-cresce-82/)
  (dados do Departamento Nacional de Estatísticas da China, o NBS):** em 2025 o
  gasto da China em P&D cresceu 8,2% e chegou a 3,93 trilhões de yuans (cerca de
  584,5 bilhões de dólares, segundo a matéria). Entre 2021 e 2025 a alta média
  foi de 10% ao ano. A intensidade de P&D subiu para 2,8% do PIB, acima da média
  da OCDE (2,72%) pela primeira vez, e a China é a segunda maior investidora do
  mundo. As empresas respondem por 77,4% do gasto total, contra 11,6% das
  instituições de pesquisa do governo e 8,7% das universidades. A pesquisa
  básica foi a que mais cresceu (13,3%, contra 3,2% da aplicada e 8,4% do
  desenvolvimento experimental). Os polos de Pequim-Tianjin-Hebei, do Delta do
  Yangtzé e de Guangdong concentram 58,8% do gasto nacional.
- **OCDE, via [AAU](https://www.aau.edu/newsroom/its-official-china-tops-us-rd-spending)
  e [Outras Palavras](https://outraspalavras.net/outrasaude/china-ultrapassa-eua-em-gastos-com-pd/)
  (06/04/2026):** em 2024 a China investiu cerca de 1,03 trilhão de dólares em
  P&D, contra 1,01 trilhão dos EUA, somando todas as fontes de financiamento. A
  Outras Palavras informa que os valores estão ajustados pela paridade do poder
  de compra (PPC); a AAU descreve a unidade de forma ambígua (fala em dólares
  correntes e, no gráfico, em PPC). Segundo a AAU, o gasto chinês equivale a
  2,7% do PIB e cresce mais de 14% ao ano desde 2004; a Outras Palavras fala em
  quase 10% ao ano na última década. Ainda segundo a Outras Palavras, os EUA
  investem 0,5% do PIB em pesquisa básica, contra 0,19% da China. Não consegui
  ver os números no documento original da OCDE: os valores vêm dessas duas
  matérias, que coincidem entre si.
- **Mudança no perfil do gasto chinês:** pelos valores da matéria, a pesquisa
  básica já é cerca de 7% do total e o desenvolvimento experimental cerca de
  81%. A carta do IEDI citava cerca de 5% e 85% (dados até 2020). É um cálculo
  nosso, a partir dos números das duas fontes. Ele é coerente com os 0,19% do
  PIB em pesquisa básica citados acima (cerca de 7% de 2,7% do PIB).
- **Cuidado ao comparar:** a NSF mede o P&D feito dentro dos EUA, em dólares; o
  IEDI e o NBS trazem o gasto nacional da China (em % do PIB e em yuans); o
  Scoreboard mede o P&D das empresas da base, em euros. As fontes servem para
  dar contexto e interpretar a tendência, não para comparar os níveis entre si.
"""
    )

with st.expander("5. Base x OCDE: por que os resultados divergem?"):
    st.markdown(
        """
Na base, o P&D da China equivale a 35% do americano em 2024. Pela OCDE, a China
já passou os EUA. As duas leituras podem estar certas, porque medem coisas
diferentes:

- **Conversão de moeda:** a OCDE usa a paridade do poder de compra (PPC), que em
  geral valoriza o gasto de países com custos internos menores. A base usa euros.
  O Monitor Mercantil, a câmbio corrente, converte o gasto chinês de 2025 em
  cerca de 584,5 bilhões de dólares, bem abaixo de 1,03 trilhão em PPC (anos e
  métodos diferentes, mas mostra o efeito da conversão).
- **Escopo:** a OCDE mede o P&D total feito no país (empresas, governo e
  universidades). A base cobre só as empresas que mais investem em P&D.
- **Cobertura da base:** o número de empresas chinesas cai de 738 para 535 entre
  2021 e 2024 (caixa 3).
- **Pesquisa básica:** é onde os EUA ainda lideram (0,5% x 0,19% do PIB), e a
  base não separa pesquisa básica de desenvolvimento.
"""
    )

with st.expander("6. Limites da base"):
    st.markdown(
        """
- O "total mundial" do painel é a soma das empresas da base (as que mais
  investem em P&D), e não o P&D de todo o mundo.
- A base só tem empresas. Para comparar países inteiros, como faz a OCDE, é
  preciso usar estatísticas nacionais.
- Os valores estão em milhões de euros (confirmado para P&D; confirmar para as
  demais métricas).
- A base já vem agregada por país e setor, sem empresas individuais. Por isso
  não dá para analisar empresas brasileiras ou Big Techs com esses dados.
- Na aba Sales, o valor da Colômbia em 2015 (cerca de 50 milhões) é um erro
  evidente e foi retirado do total daquele ano.
"""
    )