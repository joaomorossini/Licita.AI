import streamlit as st
import streamlit.components.v1 as components

# from src.dify_client import DifyClient


# Configure page
st.set_page_config(
    page_title="Assistente de Licitações",
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


def copy_to_clipboard(text):
    """Create a button that copies text to clipboard using JavaScript."""
    html_code = f"""
        <input type="text" value='{text}' id="myInput" style="position: absolute; left: -9999px;">
        <script>
            var copyText = document.getElementById("myInput");
            copyText.select();
            copyText.setSelectionRange(0, 99999);
            navigator.clipboard.writeText(copyText.value);
            copyText.remove();
        </script>
    """
    st.components.v1.html(html_code, height=0)


# Create DifyClient instance
# dify_client = DifyClient()

# Sidebar - Available Tenders
with st.sidebar:
    # st.info(
    #     "💡 **DICA**: Clique abaixo na licitação desejada para copiar seu Id, depois cole ao lado no campo **'id_licitacao_atual'** antes de iniciar a conversa."
    # )
    st.warning(
        """⚠️ **ATENÇÃO**:
               Esse é um protótipo com capacidades limitadas
               """
    )
    st.info(
        """
        O assistente foi alimentado apenas com informações da licitação **Sanepar ETE Faxinal 271-2024**.
        """
    )
    # st.subheader("Licitações Disponíveis")
    # try:
    #     datasets = dify_client.fetch_all_datasets()
    #     if datasets:
    #         for dataset in datasets:
    #             dataset_name = dataset["name"].replace("|", "")
    #             # Get dataset status
    #             status_type, status_icon, _ = dify_client.get_dataset_status(
    #                 dataset["id"]
    #             )

    #             # Create button with status icon
    #             button_label = f"{status_icon} {dataset_name}"
    #             if st.button(button_label, type="tertiary"):
    #                 copy_to_clipboard(dataset_name)
    #                 st.toast("Texto copiado para a área de transferência!", icon="✅")
    #     else:
    #         st.warning("Nenhuma licitação disponível.")
    #         st.info(
    #             "Crie uma nova base de conhecimento para começar, ou prossiga assim mesmo, clicando em 'Iniciar Conversa' ao lado, sem preencher o id da licitação ."
    #         )

    # except Exception as e:
    #     st.error("Erro ao carregar licitações disponíveis.")
    #     st.error(str(e))

st.title("Assistente de Licitações 💬")
st.divider()

src = "https://udify.app/chat/pDAjmEFFaYQqHags"


# Style the iframe element and hide the specific div
iframe_style = """
<style>
  #dify-iframe {
    border: 0px groove #ffffff;
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
