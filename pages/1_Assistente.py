"""Chat com Edital page."""

import streamlit as st
from src.chat_com_edital import chat_com_edital_page

# Configure page
st.set_page_config(
    page_title="Assistente de Licitações",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# st.title("Chat com Edital 📄")
# st.markdown("Converse com nosso assistente inteligente sobre editais de licitação.")

# Display the chat interface
chat_com_edital_page()
