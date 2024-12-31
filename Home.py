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
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Bem-vindo ao Licita.AI 🤖")

st.markdown(
    """
### Seu assistente inteligente para licitações

Navegue pelo menu lateral para acessar as diferentes funcionalidades:

- **📄 Assistente**: Chat inteligente para análise de editais
- **📰 Boletins**: Acompanhamento de boletins de licitação
- **📊 Dashboard**: Visualização de métricas e insights

"""
)
