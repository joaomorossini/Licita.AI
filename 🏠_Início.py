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
    page_title="Página Inicial",
    page_icon="🏠",
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

with st.sidebar:
    st.info(
        "💡 **DICA**: Para alterar o tema (*Light* ou *Dark*), clique no canto superior direito, depois em **Settings** e selecione o tema desejado"
    )

st.title("Página Inicial 🏠")
st.divider()

# Add image to the Streamlit page
image_path = "assets/licita_ai_cover.png"
if os.path.exists(image_path):
    st.image(image_path, width=1200)
else:
    st.title("Bem-vindo ao Licita.AI")

# st.divider()

st.markdown(
    """
    <br>
    <div style='text-align: center;'>
        <h4>Licita.AI: Inteligência Artificial aplicada a licitações </h4>
    </div>
    <br>
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
        **📚 Conhecimento**: Gerencie o conhecimento relacionado a cada licitação

        **📋 Resumos**: Resumo de licitação

        **📄 Assistente**: Chat inteligente para análise de editais
        """
    )

with col2:
    st.markdown(
        """
        **📰 Boletins**: Acompanhamento de boletins de licitação (*Em construção*)

        **📊 Dashboard**: Visualização de métricas e insights (*Em construção*)

        **🗣️ Feedback**: Envie seu feedback para melhorarmos a plataforma
        """
    )
