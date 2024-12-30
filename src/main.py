"""Main application module."""

import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
from src.chat_com_edital import chat_com_edital_page

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


def app_function():
    """Display the main application with navigation to Chat com Edital.

    Returns:
        bool: True if the application loads successfully
    """
    # st.title("Hello, world!")
    return chat_com_edital_page()


if __name__ == "__main__":
    app_function()
