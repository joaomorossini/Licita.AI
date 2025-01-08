"""Dashboard page."""

import streamlit as st
from datetime import datetime, timedelta

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

# Placeholder for future implementation
st.warning(
    "⚠️ Em construção. Em breve você poderá visualizar métricas e insights sobre licitações aqui."
)
