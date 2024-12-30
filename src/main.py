"""Main application module."""

import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
from src.chat_com_edital import chat_com_edital_page
from src.boletins import boletins_page

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
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
    page_title="Licita.AI", layout="wide", initial_sidebar_state="expanded"
)


def app_function():
    """Display the main application with navigation between pages."""

    # Create navigation tabs
    tab1, tab2 = st.tabs(["Chat com Edital", "Boletins"])

    with tab1:
        return chat_com_edital_page()

    with tab2:
        st.sidebar.hide()  # Hide sidebar in Boletins tab
        return boletins_page()


if __name__ == "__main__":
    app_function()
