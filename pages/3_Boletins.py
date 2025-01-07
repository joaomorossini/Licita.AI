"""Boletins page."""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

# Configure page
st.set_page_config(
    page_title="Boletins - Licita.AI",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get help": None, "Report a bug": None, "About": None},
)

# Remove top padding and reduce sidebar width
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 1rem;
        }
        section[data-testid="stSidebar"] {
            width: 18rem !important;
        }
        section[data-testid="stSidebar"] > div {
            width: 18rem;
        }
        /* Hide label for date inputs */
        .stDateInput label {
            display: none;
        }
        /* Adjust date input width */
        .stDateInput input {
            width: 100%;
            min-width: 0;
            padding: 0.4rem;
        }
        /* Vertically align date label with input */
        .date-label {
            margin-top: 0.5rem;
            font-weight: 500;
        }
        /* Add spacing after date filters */
        .date-filters {
            margin-bottom: 2rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Boletins de Oportunidades 📰")
st.divider()

# Date filters at the top
st.markdown('<div class="date-filters">', unsafe_allow_html=True)
date_cols = st.columns([1, 2, 0.5, 1, 2, 6])

# TODO: Adicionar coluna "objeto"
with date_cols[0]:
    st.markdown('<p class="date-label">De</p>', unsafe_allow_html=True)
with date_cols[1]:
    start_date = st.date_input(
        "De",
        value=datetime.now().date() - timedelta(days=30),
        max_value=datetime.now().date(),
        label_visibility="collapsed",
    )

with date_cols[3]:
    st.markdown('<p class="date-label">Até</p>', unsafe_allow_html=True)
with date_cols[4]:
    end_date = st.date_input(
        "Até",
        value=datetime.now().date(),
        max_value=datetime.now().date(),
        label_visibility="collapsed",
    )
st.markdown("</div>", unsafe_allow_html=True)

# Filters in sidebar
with st.sidebar:
    st.title("Filtros")

    # Client filter
    st.subheader("Cliente")
    selected_clients = st.multiselect(
        "Selecione os clientes",
        ["Empresa A", "Empresa B", "Empresa C", "Empresa D", "Empresa E"],
        default=[],
    )

    # Type filter
    st.subheader("Tipo")
    selected_types = st.multiselect(
        "Selecione os tipos",
        ["Licitação", "Pregão", "Concorrência"],
        default=[],
    )

    # Size filter
    st.subheader("Porte")
    selected_sizes = st.multiselect(
        "Selecione o porte",
        ["Pequeno", "Médio", "Grande"],
        default=[],
    )

    # Value range
    st.subheader("Valor de Referência")
    min_value = st.number_input(
        "Valor mínimo", min_value=0, value=0, step=10000, format="%d"
    )
    max_value = st.number_input(
        "Valor máximo", min_value=0, value=1000000, step=10000, format="%d"
    )

    # Status filter
    st.subheader("Status")
    selected_status = st.multiselect(
        "Selecione o status",
        ["Participar", "Não Participar", "Em Análise"],
        default=[],
    )

    # Apply filters button
    st.markdown("---")
    if st.button("Aplicar Filtros", type="primary", use_container_width=True):
        st.rerun()

# Results table
st.subheader("Resultados")

# Example data for the table
data = {
    "Número": ["001/2024", "002/2024", "003/2024", "004/2024", "005/2024"],
    "Cliente": ["Empresa A", "Empresa B", "Empresa C", "Empresa D", "Empresa E"],
    "Recebido em": [
        "2024-01-01",
        "2024-01-02",
        "2024-01-03",
        "2024-01-04",
        "2024-01-05",
    ],
    "Tipo": ["Licitação", "Pregão", "Concorrência", "Licitação", "Pregão"],
    "Porte": ["Pequeno", "Médio", "Grande", "Médio", "Pequeno"],
    "Valor Referência": [
        "R$ 100.000,00",
        "R$ 200.000,00",
        "R$ 300.000,00",
        "R$ 150.000,00",
        "R$ 250.000,00",
    ],
    "Decisão": [
        "Participar",
        "Não Participar",
        "Em Análise",
        "Participar",
        "Em Análise",
    ],
}

# Convert to DataFrame for better display
df = pd.DataFrame(data)

# Apply filters (if any)
if selected_clients:
    df = df[df["Cliente"].isin(selected_clients)]
if selected_types:
    df = df[df["Tipo"].isin(selected_types)]
if selected_sizes:
    df = df[df["Porte"].isin(selected_sizes)]
if selected_status:
    df = df[df["Decisão"].isin(selected_status)]

# Display the table with custom styling
st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Número": st.column_config.TextColumn(
            "Número",
            help="Número do processo",
            width="small",
        ),
        "Cliente": st.column_config.TextColumn(
            "Cliente",
            help="Nome do cliente",
            width="medium",
        ),
        "Recebido em": st.column_config.DateColumn(
            "Recebido em",
            help="Data de recebimento",
            format="DD/MM/YYYY",
            width="small",
        ),
        "Tipo": st.column_config.TextColumn(
            "Tipo",
            help="Tipo do processo",
            width="medium",
        ),
        "Porte": st.column_config.TextColumn(
            "Porte",
            help="Porte da empresa",
            width="small",
        ),
        "Valor Referência": st.column_config.TextColumn(
            "Valor Referência",
            help="Valor de referência",
            width="medium",
        ),
        "Decisão": st.column_config.TextColumn(
            "Decisão",
            help="Status da decisão",
            width="small",
        ),
    },
)