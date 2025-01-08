"""Dashboard page."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# Configure page
st.set_page_config(
    page_title="Dashboard - Licita.AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get help": None, "Report a bug": None, "About": None},
)

# Remove top padding and reduce sidebar width
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 1.5rem;
        }
        section[data-testid="stSidebar"] {
            width: 18rem !important;
        }
        section[data-testid="stSidebar"] > div {
            width: 18rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Dashboard 📊")
st.divider()

st.warning("⚠️ Em construção. Este é um dashboard de exemplo e os dados são fictícios.")

# Sidebar filters
with st.sidebar:
    st.markdown(
        """
        <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
        <h1 style="display: flex; align-items: center;">
            Filtros&nbsp<span class="material-icons">filter_alt</span>
        </h1>
        """,
        unsafe_allow_html=True,
    )

    # Time range
    st.subheader("Período")
    time_range = st.selectbox(
        "Selecione o período",
        [
            "Últimos 30 dias",
            "Último trimestre",
            "Último semestre",
            "Último ano",
            "Personalizado",
        ],
    )

    if time_range == "Personalizado":
        start_date = st.date_input(
            "De",
            value=datetime.now().date() - timedelta(days=30),
            max_value=datetime.now().date(),
        )
        end_date = st.date_input(
            "Até",
            value=datetime.now().date(),
            max_value=datetime.now().date(),
        )

    # View type
    st.subheader("Visualização")
    view_type = st.radio(
        "Tipo de visualização", ["Geral", "Por Cliente", "Por Tipo", "Por Região"]
    )

    # Metrics selection
    st.subheader("Métricas")
    metrics = st.multiselect(
        "Selecione as métricas",
        [
            "Valor Total",
            "Quantidade de Editais",
            "Taxa de Participação",
            "Taxa de Sucesso",
            "Tempo Médio de Análise",
        ],
        default=["Valor Total", "Quantidade de Editais"],
    )

    # Comparison
    st.subheader("Comparação")
    compare_with = st.multiselect(
        "Comparar com", ["Período Anterior", "Meta", "Média do Mercado"], default=[]
    )

    # Apply filters button
    if st.button("Atualizar Dashboard", type="primary", use_container_width=True):
        st.rerun()

# Generate mock data
dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="D")
values = np.random.normal(1000000, 200000, len(dates))
tenders = np.random.randint(1, 10, len(dates))
df = pd.DataFrame({"Data": dates, "Valor": values, "Quantidade": tenders})

# Monthly aggregation
df_monthly = (
    df.set_index("Data")
    .resample("M")
    .agg({"Valor": "sum", "Quantidade": "sum"})
    .reset_index()
)

# Create mock data for other visualizations
regions = ["Sul", "Sudeste", "Centro-Oeste", "Norte", "Nordeste"]
region_values = np.random.randint(5000000, 50000000, len(regions))
region_quantities = np.random.randint(20, 200, len(regions))

tender_types = ["Obras", "Serviços", "Materiais", "Equipamentos", "Outros"]
type_values = np.random.randint(1000000, 10000000, len(tender_types))

# KPI metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Valor Total de Licitações",
        f"R$ {df['Valor'].sum()/1e6:.1f}M",
        "12.5%",
        help="Valor total de todas as licitações no período selecionado",
    )

with col2:
    st.metric(
        "Quantidade de Editais",
        f"{df['Quantidade'].sum()}",
        "-4.2%",
        help="Número total de editais analisados no período",
    )

with col3:
    st.metric(
        "Taxa de Participação",
        "68.5%",
        "8.1%",
        help="Percentual de editais em que houve participação",
    )

with col4:
    st.metric(
        "Taxa de Sucesso",
        "42.3%",
        "15.4%",
        help="Percentual de licitações vencidas entre as participadas",
    )

# Charts row 1
col1, col2 = st.columns(2)

with col1:
    st.subheader("Valor Total de Licitações por Mês")
    fig = px.bar(
        df_monthly,
        x="Data",
        y="Valor",
        labels={"Data": "Mês", "Valor": "Valor Total (R$)"},
        template="plotly_white",
    )
    fig.update_layout(
        height=400,
        hovermode="x unified",
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Distribuição por Região")
    fig = px.pie(
        values=region_values,
        names=regions,
        hole=0.4,
        template="plotly_white",
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# Charts row 2
col1, col2 = st.columns(2)

with col1:
    st.subheader("Quantidade de Editais por Mês")
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_monthly["Data"],
            y=df_monthly["Quantidade"],
            mode="lines+markers",
            name="Quantidade",
            line=dict(width=3),
        )
    )
    fig.update_layout(
        height=400,
        template="plotly_white",
        hovermode="x unified",
        showlegend=False,
        yaxis_title="Quantidade de Editais",
        xaxis_title="Mês",
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Valor por Tipo de Licitação")
    df_types = pd.DataFrame({"Tipo": tender_types, "Valor": type_values})
    fig = px.bar(
        df_types,
        x="Tipo",
        y="Valor",
        labels={"Valor": "Valor Total (R$)"},
        template="plotly_white",
    )
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# Data table
st.subheader("Últimas Licitações")
df_table = pd.DataFrame(
    {
        "Data": pd.date_range(end=datetime.now(), periods=5, freq="D"),
        "Órgão": [
            "Prefeitura de São Paulo",
            "Governo do Estado RS",
            "Ministério da Saúde",
            "Prefeitura de Curitiba",
            "DNIT",
        ],
        "Objeto": [
            "Construção de Hospital",
            "Fornecimento de Medicamentos",
            "Serviços de Limpeza",
            "Manutenção de Escolas",
            "Pavimentação de Rodovia",
        ],
        "Valor Estimado": np.random.randint(100000, 5000000, 5),
        "Status": [
            "Em Análise",
            "Participando",
            "Vencida",
            "Em Análise",
            "Não Participar",
        ],
    }
)

st.dataframe(
    df_table.style.format({"Valor Estimado": "R$ {:,.2f}"}),
    hide_index=True,
    use_container_width=True,
)
