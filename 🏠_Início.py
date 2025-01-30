"""Main page of the Licita.AI application."""

import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
import streamlit.components.v1 as components

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Configure page
st.set_page_config(
    page_title="Página Inicial",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": None,
    },
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

# Center the title and subtitle
st.markdown(
    """
    <div style="text-align: center;">
        <h1>Licita.AI</h1>
        <h4>Inteligência artificial aplicada a licitações</h4>
    </div>
    <br>
    """,
    unsafe_allow_html=True,
)
st.divider()

# Add custom CSS for styling the divs
st.markdown(
    """
    <style>
        .page-link-div {
            height: 200px;
            width: 275px;
            border: 2px solid #E2E8F0;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            cursor: pointer;
            background-color: #2D3748;
        }
        .page-link-div:hover {
            color: #6B46C1;
            border-color: #6B46C1;
        }
        .page-link-div a {
            font-size: 40px;
            text-decoration: none;
            color: inherit;
        }
        .page-link-div a:hover {
            color: #6B46C1;
        }
        .page-link-div p {
            font-size: 18px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3, col4, col5 = st.columns(5)

with col2:
    with st.container():
        st.write("""<div class="page-link-div">
                        <a href='/Resumos' class="custom-page-link" target="_self">📝 Resumos</a>
                    </div>""", unsafe_allow_html=True)

with col3:
    with st.container():
        st.write("""<div class="page-link-div">
                        <a href='/Assistente' class="custom-page-link" target="_self">🧠 Assistente</a>
                    </div>""", unsafe_allow_html=True)

with col4:
    with st.container():
        st.write("""<div class="page-link-div">
                        <a href='/Boletins' class="custom-page-link" target="_self">📰 Boletins</a>
                    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col2:
    with st.container():
        st.write("""<div class="page-link-div">
                        <a href='/Dashboard' class="custom-page-link" target="_self">📊 Dashboard</a>
                    </div>""", unsafe_allow_html=True)

with col3:
    with st.container():
        st.write("""<div class="page-link-div">
                        <a href='/Feedback' class="custom-page-link" target="_self">🗣️ Feedback</a>
                    </div>""", unsafe_allow_html=True)
