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
)

st.title("Boletins 📰")
st.markdown("Acompanhe os boletins de licitação mais recentes.")

# Clear the sidebar for this tab
st.sidebar.empty()

# Filters section at the top
st.subheader("Filtros")

# Date filters in columns
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    start_date = st.date_input(
        "De",
        value=datetime.now().date() - timedelta(days=30),
        max_value=datetime.now().date(),
    )

with col2:
    end_date = st.date_input(
        "Até",
        value=datetime.now().date(),
        max_value=datetime.now().date(),
    )

# Results table
st.subheader("Resultados")

# Example data for the table with all columns from wireframe
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
