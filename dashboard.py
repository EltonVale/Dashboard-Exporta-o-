#---------------------------------------------------------------------
# PASSO 1: INSTALAÇÃO (Execute no terminal antes de rodar)
# pip install streamlit plotly
#
# PASSO 2: EXECUTAR (Execute no terminal para iniciar)
# streamlit run dashboard.py
#---------------------------------------------------------------------

import streamlit as st
import plotly.graph_objects as go
import locale

# --- DADOS PROCESSADOS (Embutidos para este script funcionar) ---
# (Estes dados foram extraídos da sua planilha)

data_am = {
    'total_linhas': 100,
    'concluido': {
        'LONGO CURSO': {'ops': 71, 'volume': 18820.865, 'valor': 73250396.52},
        'CABOTAGEM':   {'ops': 19, 'volume': 4282.328,  'valor': 4743682.28}
    }
}

data_pa = {
    'total_linhas': 40,
    'concluido': {
        'LONGO CURSO': {'ops': 27, 'volume': 5893.27,  'valor': 20274843.06},
        'CABOTAGEM':   {'ops': 2,  'volume': 1000.788, 'valor': 0.0}
    }
}

# --- CONFIGURAÇÃO DA PÁGINA (Layout Executivo) ---
st.set_page_config(layout="wide", page_title="Dashboard Bunker")

# --- FUNÇÕES AUXILIARES DE FORMATAÇÃO ---
def format_reais(valor):
    """Formata um número como moeda BRL."""
    try:
        # Define o locale para o padrão brasileiro para formatação
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
        return locale.currency(valor, grouping=True, symbol='R$')
    except:
        # Fallback caso o locale pt_BR não esteja instalado no sistema
        return f"R$ {valor:,.2f}"

def format_numero(valor, casas_decimais=0):
    """Formata um número com separador de milhar."""
    return f"{valor:,.{casas_decimais}f}"

# --- CSS CUSTOMIZADO (Minimalista e Executivo) ---
# (Isso oculta o menu "Made with Streamlit" e ajusta o padding)
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
    }
    .stMetric {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 15px 20px;
    }
    .stMetric .css-1xarl3l, .stMetric .css-1xarl3l {
        color: #5a7184; /* Cor do título (label) */
    }
</style>
""", unsafe_allow_html=True)


# --- CÁLCULO DOS TOTAIS ---
am_concluido = data_am['concluido']
pa_concluido = data_pa['concluido']

total_valor = am_concluido['LONGO CURSO']['valor'] + am_concluido['CABOTAGEM']['valor'] + \
              pa_concluido['LONGO CURSO']['valor'] + pa_concluido['CABOTAGEM']['valor']
              
total_volume = am_concluido['LONGO CURSO']['volume'] + am_concluido['CABOTAGEM']['volume'] + \
               pa_concluido['LONGO CURSO']['volume'] + pa_concluido['CABOTAGEM']['volume']

total_processos = data_am['total_linhas'] + data_pa['total_linhas']


# --- TÍTULO DO DASHBOARD ---
st.title("Dashboard Executivo de Performance Bunker")
st.markdown("Visão consolidada das operações de bunker no Amazonas (AM) e Pará (PA) para 2025.")
st.divider()

# --- 1. VISÃO GERAL (KPIs Principais) ---
st.header("Visão Geral Consolidada (AM + PA)")

cols_kpi = st.columns(3)
with cols_kpi[0]:
    st.metric(
        label="Valor Total (Operações Concluídas)", 
        value=format_reais(total_valor)
    )
with cols_kpi[1]:
    st.metric(
        label="Volume Total (Operações Concluídas)", 
        value=f"{format_numero(total_volume, 2)} TON"
    )
with cols_kpi[2]:
    st.metric(
        label="Total de Processos (Todas as Linhas)", 
        value=format_numero(total_processos)
    )

st.divider()

# --- 2. ANÁLISE REGIONAL (Lado a Lado) ---
st.header("Análise Regional Detalhada")
col_am, col_pa = st.columns(2)

# --- COLUNA AMAZONAS (AM) ---
with col_am:
    st.subheader("Amazonas (AM)")
    
    # KPIs Regionais AM
    st.metric(
        label="Total de Processos (Linhas)",
        value=format_numero(data_am['total_linhas'])
    )
    
    kpi_am_1, kpi_am_2 = st.columns(2)
    with kpi_am_1:
        st.metric(
            label="Valor Exportado (Longo Curso)",
            value=format_reais(am_concluido['LONGO CURSO']['valor'])
        )
    with kpi_am_2:
        st.metric(
            label="Valor Interno (Cabotagem)",
            value=format_reais(am_concluido['CABOTAGEM']['valor'])
        )

    # Gráfico Interativo (Plotly)
    labels_am = ['Longo Curso', 'Cabotagem']
    values_am = [am_concluido['LONGO CURSO']['ops'], am_concluido['CABOTAGEM']['ops']]
    colors_am = ['#0056b3', '#1e8449']

    fig_am = go.Figure(data=[go.Pie(
        labels=labels_am, 
        values=values_am, 
        hole=.5, 
        marker_colors=colors_am,
        textinfo='value+percent',
        hoverinfo='label+value'
    )])
    fig_am.update_layout(
        title_text='Operações Concluídas por Tipo (AM)',
        title_x=0.5,
        margin=dict(t=50, b=10, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        font=dict(color="#2c3e50")
    )
    st.plotly_chart(fig_am, use_container_width=True)

# --- COLUNA PARÁ (PA) ---
with col_pa:
    st.subheader("Pará (PA)")
    
    # KPIs Regionais PA
    st.metric(
        label="Total de Processos (Linhas)",
        value=format_numero(data_pa['total_linhas'])
    )
    
    kpi_pa_1, kpi_pa_2 = st.columns(2)
    with kpi_pa_1:
        st.metric(
            label="Valor Exportado (Longo Curso)",
            value=format_reais(pa_concluido['LONGO CURSO']['valor'])
        )
    with kpi_pa_2:
        st.metric(
            label="Valor Interno (Cabotagem)",
            value=format_reais(pa_concluido['CABOTAGEM']['valor'])
        )

    # Gráfico Interativo (Plotly)
    labels_pa = ['Longo Curso', 'Cabotagem']
    values_pa = [pa_concluido['LONGO CURSO']['ops'], pa_concluido['CABOTAGEM']['ops']]
    colors_pa = ['#0056b3', '#1e8449']

    fig_pa = go.Figure(data=[go.Pie(
        labels=labels_pa, 
        values=values_pa, 
        hole=.5, 
        marker_colors=colors_pa,
        textinfo='value+percent',
        hoverinfo='label+value'
    )])
    fig_pa.update_layout(
        title_text='Operações Concluídas por Tipo (PA)',
        title_x=0.5,
        margin=dict(t=50, b=10, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        font=dict(color="#2c3e50")
    )
    st.plotly_chart(fig_pa, use_container_width=True)