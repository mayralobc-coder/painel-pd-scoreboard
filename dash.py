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
st.header("Análise dos Resultados")

texto_analise = """
A dinâmica do desenvolvimento tecnológico contemporâneo é marcada por um processo profundo de reconfiguração geopolítica. Ao longo das últimas duas décadas, assistimos à transição de uma hegemonia dos Estados Unidos para um cenário de concorrência global cada vez mais acirrada com a China. A trajetória traçada pelos dados de Pesquisa e Desenvolvimento (P&D) no período de 2003 a 2024 reflete esse movimento: enquanto o investimento norte-americano manteve um crescimento robusto em termos absolutos — aproximando-se da marca de €700 bilhões anuais —, a China protagonizou um processo vertiginoso de convergência tecnológica. 

Em 2005, o ecossistema corporativo chinês representava meros 0,7% da base mundial analisada, o equivalente a apenas 2% do volume gasto pelos EUA. Duas décadas depois, a participação chinesa saltou para 16,0%, alcançando 35% do montante despendido pelas grandes empresas norte-americanas. Quando são observados os dados nacionais consolidados, ajustados pela Paridade de Poder de Compra (PPC) e somando os aportes governamentais, os diagnósticos internacionais já apontam a ultrapassagem da China sobre o orçamento total norte-americano de P&D. Apesar dessa rápida ascensão quantitativa, a análise pormenorizada das métricas corporativas revela assimetrias estruturais marcantes entre os dois modelos de inovação. 

No que tange à infraestrutura de pesquisa, a China superou o volume bruto de recursos humanos dos Estados Unidos ainda em 2015 — alcançando, em 2024, uma força de trabalho científica 1,28 vez maior que a norte-americana — além de ter registrado momentos de liderança nas despesas de capital (Capex). Contudo, a economia norte-americana preserva uma vantagem substancial em termos de intensidade tecnológica e retorno financeiro. Enquanto a intensidade de P&D corporativo nos EUA subiu de 4,3% para 8,8% das receitas entre 2005 e 2024, a taxa chinesa evoluiu de 0,7% para 4,0%. Da mesma forma, o investimento médio por empresa nos EUA ultrapassa €1 bilhão, contra cerca de €437 milhões por firma chinesa. Esse contraste evidencia que, enquanto os EUA sustentam seu domínio baseados na alta concentração de capital em gigantes de tecnologia (big techs) com elevada margem de lucro e forte valorização de mercado — onde detêm 58,4% da capitalização global —, o avanço chinês ancora-se em uma base industrial extremamente pulverizada e em forte expansão estatal. 

Por fim, esse fenômeno reflete a transição estrutural da China de uma economia voltada à assimilação de tecnologias estrangeiras para uma estratégia focada na autossuficiência e soberania tecnológica em setores estratégicos, como inteligência artificial, semicondutores e energia limpa. Por outro lado, a distância nas métricas de valor de mercado e intensidade de P&D evidencia o peso das diferenças setoriais: os EUA lideram áreas de altíssimo valor agregado intangível, como software e biotecnologia, ao passo que a China ainda carrega um peso expressivo da manufatura tradicional em seu PIB industrial. Por outro lado, a sustentação das altas taxas de crescimento do P&D chinês aponta para um cenário bipolar definitivo: de um lado, a eficiência e o valor de mercado hegemonizados pelos EUA; do outro, a capacidade massiva de mobilização e escala do modelo chinês.
"""

with st.expander("📖 Ler Análise Consolidada da Reconfiguração Geopolítica (2003–2024)", expanded=True):
    st.markdown(texto_analise)    
