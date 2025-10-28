#---------------------------------------------------------------------
# PASSO 1: INSTALAÇÃO (Execute no terminal antes de rodar)
# python -m pip install -r requirements.txt
#
# PASSO 2: EXECUTAR (Use este comando no terminal para iniciar)
# python -m streamlit run dashboard.py
#---------------------------------------------------------------------

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import os # Para verificar se os arquivos existem
import math # Para ajudar na formatação
import re # Para limpeza mais avançada

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Dashboard Exportação Bunker")

# --- CSS CUSTOMIZADO (Minimalista e SEGURO para Temas) ---
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
    /* Estilo dos cards de KPI */
    .stMetric {
        background-color: #FFFFFF; /* Garante fundo branco mesmo em tema escuro */
        border: 1px solid #eaf0f6;
        border-radius: 10px;
        padding: 15px 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    }
     /* Ajusta a cor do label do KPI */
    .stMetric > label {
         color: #5a7184; /* Tom de cinza mais escuro */
    }
    /* Ajusta a cor do valor principal */
     .stMetric > div > div > span {
         color: #1a237e; /* Azul escuro */
    }
</style>
""", unsafe_allow_html=True)


# --- FUNÇÕES AUXILIARES DE FORMATAÇÃO ---
def format_reais(valor):
    """Formata um número como moeda BRL (ex: R$ 93.525.239,80) de forma robusta."""
    if valor is None or not isinstance(valor, (int, float)):
        return "R$ 0,00"
    try:
        valor_arredondado = round(valor, 2)
        parte_inteira = int(math.floor(valor_arredondado))
        parte_decimal = int(round((valor_arredondado - parte_inteira) * 100))
        parte_inteira_formatada = f"{parte_inteira:,}".replace(",", ".")
        parte_decimal_formatada = f"{parte_decimal:02d}"
        return f"R$ {parte_inteira_formatada},{parte_decimal_formatada}"
    except Exception:
        return f"R$ {valor:.2f}" # Fallback

def format_numero(valor, casas_decimais=0):
    """Formata um número com separador de milhar (ex: 30.997,25) de forma robusta."""
    if valor is None or not isinstance(valor, (int, float)):
        return "0"
    try:
        multiplicador = 10 ** casas_decimais
        valor_arredondado = round(valor, casas_decimais)
        parte_inteira = int(math.floor(valor_arredondado))
        parte_decimal = int(round((valor_arredondado - parte_inteira) * multiplicador))
        parte_inteira_formatada = f"{parte_inteira:,}".replace(",", ".")

        if casas_decimais > 0:
            formato_decimal = f"{{:0{casas_decimais}d}}"
            parte_decimal_formatada = formato_decimal.format(parte_decimal)
            return f"{parte_inteira_formatada},{parte_decimal_formatada}"
        else:
            return parte_inteira_formatada
    except Exception:
        return f"{valor:.{casas_decimais}f}" # Fallback

#
# ------------------- NOVA FUNÇÃO DE LIMPEZA NUMÉRICA MAIS ROBUSTA -------------------
#
def limpar_e_converter(texto):
    """Tenta converter texto para float de forma mais robusta, exibindo avisos."""
    if texto is None: return 0.0
    s = str(texto).strip()
    if not s or s == '-': return 0.0

    # 1. Remove caracteres comuns não numéricos (exceto , . e - no início)
    s_limpa = re.sub(r"[^0-9,\.-]", "", s)
    if not s_limpa: return 0.0

    # 2. Verifica se há múltiplos pontos ou vírgulas
    num_commas = s_limpa.count(',')
    num_dots = s_limpa.count('.')

    # 3. Decide qual é o separador decimal (o último encontrado)
    last_comma = s_limpa.rfind(',')
    last_dot = s_limpa.rfind('.')

    if num_commas > 1 and num_dots > 1: # Formato muito estranho
        st.warning(f"Formato numérico ambíguo zerado: '{texto}'")
        return 0.0
    
    decimal_separator = None
    if last_comma > last_dot:
        decimal_separator = ','
    elif last_dot > last_comma:
        decimal_separator = '.'
    elif num_commas == 1 and num_dots == 0: # Apenas vírgula presente
         decimal_separator = ','
    elif num_dots == 1 and num_commas == 0: # Apenas ponto presente
         decimal_separator = '.'
    # Se não houver separador, ou múltiplos do mesmo tipo sem o outro, assume que não há decimais

    # 4. Remove separadores de milhar e padroniza decimal para ponto
    if decimal_separator == ',':
        s_padronizada = s_limpa.replace('.', '').replace(',', '.')
    elif decimal_separator == '.':
        s_padronizada = s_limpa.replace(',', '')
    else: # Sem separador decimal claro ou formato inválido
        s_padronizada = s_limpa.replace(',', '').replace('.', '') # Remove tudo

    # 5. Tenta a conversão final
    try:
        val = float(s_padronizada)
        # Verificação de sanidade
        if abs(val) > 1e12: # Limite de 1 trilhão
            st.warning(f"Valor numérico muito alto zerado (possível erro): '{texto}' -> {s_padronizada}")
            return 0.0
        return val
    except ValueError:
        # Se falhar, exibe um aviso no dashboard
        st.warning(f"Não foi possível converter '{texto}' para número (resultado após limpeza: '{s_padronizada}'). Verifique o formato no Excel.")
        return 0.0
#
# ------------------- FIM DA NOVA FUNÇÃO -------------------
#

# --- CARREGAMENTO E LIMPEZA DOS DADOS ---
@st.cache_data # Usa cache para não recarregar os arquivos a cada filtro
def load_data():

    file_workbook = '1.Follow Up Export REAM 2025.1.xlsx'
    sheet_am = 'Bunker - AM'
    sheet_pa = 'Bunker - PA'

    if not os.path.exists(file_workbook):
        st.error(f"Erro: Arquivo Excel '{file_workbook}' não encontrado.")
        return pd.DataFrame(), pd.DataFrame()

    try:
        # Lê as abas, forçando colunas problemáticas a serem lidas como texto (object)
        dtype_map = {'VALOR TOTAL REAL': str, 'VOLUME CARREGADO': str}
        df_am = pd.read_excel(file_workbook, sheet_name=sheet_am, engine='openpyxl', dtype=dtype_map)
        df_pa = pd.read_excel(file_workbook, sheet_name=sheet_pa, engine='openpyxl', dtype=dtype_map)

    except Exception as e:
        st.error(f"Erro ao ler as abas do arquivo Excel: {e}")
        st.error(f"Verifique se o arquivo '{file_workbook}' não está corrompido e se as abas '{sheet_am}' e '{sheet_pa}' existem.")
        return pd.DataFrame(), pd.DataFrame()

    df_am['Regional'] = 'AM'
    df_pa['Regional'] = 'PA'
    df_full_raw = pd.concat([df_am, df_pa], ignore_index=True)

    colunas_necessarias = ['VALOR TOTAL REAL', 'VOLUME CARREGADO', 'TIPO DE NAVEGAÇÃO', 'STATUS']
    colunas_ausentes = [col for col in colunas_necessarias if col not in df_full_raw.columns]
    if colunas_ausentes:
        st.error(f"Erro Crítico: Colunas {colunas_ausentes} não encontradas.")
        return pd.DataFrame(), pd.DataFrame()

    # Aplica a nova função de limpeza MAIS ROBUSTA
    df_full_raw['VALOR TOTAL REAL'] = df_full_raw['VALOR TOTAL REAL'].apply(limpar_e_converter)
    df_full_raw['VOLUME CARREGADO'] = df_full_raw['VOLUME CARREGADO'].apply(limpar_e_converter)

    df_full_raw['TIPO DE NAVEGAÇÃO'] = df_full_raw['TIPO DE NAVEGAÇÃO'].astype(str).str.strip()
    df_full_raw['STATUS'] = df_full_raw['STATUS'].astype(str).str.strip()

    df_concluido = df_full_raw[df_full_raw['STATUS'].str.startswith('CONCLUÍDO', na=False)].copy()

    return df_full_raw, df_concluido

# Carrega os dados
df_raw_total, df_concluido_total = load_data()

if df_raw_total.empty:
    st.stop()

# --- BARRA LATERAL DE FILTROS ---
st.sidebar.header("Filtros") # Título mais sutil

regioes_disponiveis = sorted(df_raw_total['Regional'].unique())
default_regioes = list(regioes_disponiveis) if regioes_disponiveis else []
regiao_selecionada = st.sidebar.multiselect(
    "Regional", options=regioes_disponiveis, default=default_regioes
)

tipos_disponiveis = sorted(df_raw_total['TIPO DE NAVEGAÇÃO'].unique())
default_tipos = list(tipos_disponiveis) if tipos_disponiveis else []
tipo_selecionado = st.sidebar.multiselect(
    "Tipo de Navegação", options=tipos_disponiveis, default=default_tipos
)

# --- FILTRAGEM DINÂMICA DOS DADOS ---
if not regiao_selecionada: regiao_selecionada = default_regioes
if not tipo_selecionado: tipo_selecionado = default_tipos

df_raw_filtrado = df_raw_total[
    (df_raw_total['Regional'].isin(regiao_selecionada)) &
    (df_raw_total['TIPO DE NAVEGAÇÃO'].isin(tipo_selecionado))
].copy()

df_concluido_filtrado = df_concluido_total[
    (df_concluido_total['Regional'].isin(regiao_selecionada)) &
    (df_concluido_total['TIPO DE NAVEGAÇÃO'].isin(tipo_selecionado))
].copy()

# --- CÁLCULO DOS TOTAIS (DINÂMICO) ---
total_valor = df_concluido_filtrado['VALOR TOTAL REAL'].sum()
total_volume = df_concluido_filtrado['VOLUME CARREGADO'].sum()
total_processos = len(df_raw_filtrado)

# --- LAYOUT DO DASHBOARD ---

st.title("Dashboard Exportação Bunker") # Título atualizado

subtitulo_regiao = "AM & PA" if set(regioes_disponiveis).issubset(set(regiao_selecionada)) else ', '.join(regiao_selecionada)
subtitulo_tipo = "Todos os Tipos" if set(tipos_disponiveis).issubset(set(tipo_selecionado)) else ', '.join(tipo_selecionado)
st.caption(f"Exibindo dados para: **{subtitulo_regiao}** | **{subtitulo_tipo}**")
st.divider()

# --- 1. VISÃO GERAL (KPIs Principais) ---
st.header("Visão Geral")

cols_kpi = st.columns(3)
with cols_kpi[0]:
    st.metric(label="Valor Total (Concluído)", value=format_reais(total_valor))
with cols_kpi[1]:
    st.metric(label="Volume Total (Concluído)", value=f"{format_numero(total_volume, 2)} TON")
with cols_kpi[2]:
    st.metric(label="Total de Processos (Linhas)", value=format_numero(total_processos))

st.divider()

# --- 2. ANÁLISE REGIONAL (Lado a Lado) ---
st.header("Análise Regional")
col_am, col_pa = st.columns(2, gap="large")

# --- COLUNA AMAZONAS (AM) ---
with col_am:
    st.subheader("Amazonas (AM)")

    df_am_concluido = df_concluido_filtrado[df_concluido_filtrado['Regional'] == 'AM']
    df_am_raw = df_raw_filtrado[df_raw_filtrado['Regional'] == 'AM']

    am_processos = len(df_am_raw)
    am_valor_longo = df_am_concluido.loc[df_am_concluido['TIPO DE NAVEGAÇÃO'] == 'LONGO CURSO', 'VALOR TOTAL REAL'].sum()
    am_valor_cabotagem = df_am_concluido.loc[df_am_concluido['TIPO DE NAVEGAÇÃO'] == 'CABOTAGEM', 'VALOR TOTAL REAL'].sum()

    st.metric(label="Processos (Linhas)", value=format_numero(am_processos))

    kpi_am_1, kpi_am_2 = st.columns(2)
    with kpi_am_1: st.metric(label="Valor Longo Curso", value=format_reais(am_valor_longo))
    with kpi_am_2: st.metric(label="Valor Cabotagem", value=format_reais(am_valor_cabotagem))

    ops_am_longo = len(df_am_concluido[df_am_concluido['TIPO DE NAVEGAÇÃO'] == 'LONGO CURSO'])
    ops_am_cabotagem = len(df_am_concluido[df_am_concluido['TIPO DE NAVEGAÇÃO'] == 'CABOTAGEM'])

    if ops_am_longo > 0 or ops_am_cabotagem > 0:
        fig_am = go.Figure(data=[go.Pie(
            labels=['Longo Curso', 'Cabotagem'], values=[ops_am_longo, ops_am_cabotagem],
            hole=.6, marker_colors=['#0056b3', '#20c997'],
            textinfo='value+percent', hoverinfo='label+value',
            insidetextorientation='radial'
        )])
        fig_am.update_layout(
            title_text='Operações Concluídas (AM)', title_x=0.5,
            margin=dict(t=50, b=20, l=20, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
            font=dict(family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_am, use_container_width=True)
    else:
        st.info("Nenhuma operação concluída para exibir (AM).")

# --- COLUNA PARÁ (PA) ---
with col_pa:
    st.subheader("Pará (PA)")

    df_pa_concluido = df_concluido_filtrado[df_concluido_filtrado['Regional'] == 'PA']
    df_pa_raw = df_raw_filtrado[df_raw_filtrado['Regional'] == 'PA']

    pa_processos = len(df_pa_raw)
    pa_valor_longo = df_pa_concluido.loc[df_pa_concluido['TIPO DE NAVEGAÇÃO'] == 'LONGO CURSO', 'VALOR TOTAL REAL'].sum()
    pa_valor_cabotagem = df_pa_concluido.loc[df_pa_concluido['TIPO DE NAVEGAÇÃO'] == 'CABOTAGEM', 'VALOR TOTAL REAL'].sum()

    st.metric(label="Processos (Linhas)", value=format_numero(pa_processos))

    kpi_pa_1, kpi_pa_2 = st.columns(2)
    with kpi_pa_1: st.metric(label="Valor Longo Curso", value=format_reais(pa_valor_longo))
    with kpi_pa_2: st.metric(label="Valor Cabotagem", value=format_reais(pa_valor_cabotagem))

    ops_pa_longo = len(df_pa_concluido[df_pa_concluido['TIPO DE NAVEGAÇÃO'] == 'LONGO CURSO'])
    ops_pa_cabotagem = len(df_pa_concluido[df_pa_concluido['TIPO DE NAVEGAÇÃO'] == 'CABOTAGEM'])

    if ops_pa_longo > 0 or ops_pa_cabotagem > 0:
        fig_pa = go.Figure(data=[go.Pie(
            labels=['Longo Curso', 'Cabotagem'], values=[ops_pa_longo, ops_pa_cabotagem],
            hole=.6, marker_colors=['#0056b3', '#20c997'],
            textinfo='value+percent', hoverinfo='label+value',
            insidetextorientation='radial'
        )])
        fig_pa.update_layout(
            title_text='Operações Concluídas (PA)', title_x=0.5,
            margin=dict(t=50, b=20, l=20, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
            font=dict(family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_pa, use_container_width=True)
    else:
        st.info("Nenhuma operação concluída para exibir (PA).")