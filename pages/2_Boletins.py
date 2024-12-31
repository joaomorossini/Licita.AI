"""Boletins page."""

import streamlit as st
from src.boletins import boletins_page

# Configure page
st.set_page_config(
    page_title="Boletins - Licita.AI",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Boletins 📰")
st.markdown("Acompanhe os boletins de licitação mais recentes.")

# Display the bulletins interface
boletins_page()
