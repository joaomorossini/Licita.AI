import streamlit as st
import streamlit.components.v1 as components


# Configure page
st.set_page_config(
    page_title="Assistente de Licitações",
    page_icon="📄",
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

st.title("Assistente de Licitações 💬")
st.divider()

src = "https://udify.app/chat/pDAjmEFFaYQqHags"


# Style the iframe element and hide the specific div
iframe_style = """
<style>
  #dify-iframe {
    border: 5px groove #ffffff;
    border-radius: 8px;
    width: 100%;
    height: 575px;
  }
</style>
"""

# Embed the iframe with styling
components.html(
    f"""
  {iframe_style}
  <iframe id="dify-iframe" src={src} allow="microphone"></iframe>
""",
    height=640,
)
