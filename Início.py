"""Main page of the Licita.AI application."""

import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Verify required environment variables
required_vars = ["DIFY_API_KEY", "DIFY_KNOWLEDGE_API_KEY", "DIFY_API_URL"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise EnvironmentError(
        f"Missing required environment variables: {', '.join(missing_vars)}"
    )

# Configure page
st.set_page_config(
    page_title="Licita.AI",
    page_icon="🧠",
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
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Página Inicial")
# st.divider()

# Add image to the Streamlit page
image_path = "/Users/morossini/Projects/Licita.AI/assets/licita_ai_cover.png"
if os.path.exists(image_path):
    st.image(image_path, width=1200)
else:
    st.title("Bem-vindo ao Licita.AI")

st.divider()

st.markdown(
    """\n
    ##### Licita.AI 🧠: Inteligência Artificial aplicada a licitações

**📚 Conhecimento**: Gerencie o conhecimento relacionado a cada licitação

**📄 Assistente**: Chat inteligente para análise de editais

**📋 Resumo**: Resumo de licitação

**📰 Boletins**: Acompanhamento de boletins de licitação (Em construção)

**📊 Dashboard**: Visualização de métricas e insights (Em construção)
"""
)
