import os
import tempfile
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from src.dify_client import DifyClient

load_dotenv()


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

with st.sidebar:
    st.info(
        "💡 **DICA**: Lembre-se sempre de especificar sobre qual licitação você deseja conversar, assim o agente saberá onde buscar as informações relevantes."
    )

st.title("Assistente de Licitações 💬")
st.divider()

# TODO: Apply styling to the iframe to match the app's design
# Embed the iframe with styling
iframe_style = """
<style>
  #dify-iframe {
    border: 0px groove #ffffff;
    border-radius: 8px;
    width: 100%;
    height: 600px;
  }
</style>
"""

src = os.getenv("DIFY_APP_SRC")

components.html(
    f"""
  {iframe_style}
  <iframe id="dify-iframe" src={src} allow="microphone"></iframe>
""",
    height=600,
)

st.divider()

st.subheader("Criar Nova Base de Conhecimento")

# Initialize Dify client
dify_client = DifyClient()

# Initialize session state for form data
if "cliente" not in st.session_state:
    st.session_state.cliente = ""
if "referencia" not in st.session_state:
    st.session_state.referencia = ""
if "id_licitacao" not in st.session_state:
    st.session_state.id_licitacao = ""
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = None

# Form for new tender
with st.container():
    col1, col2, col3 = st.columns(3)

    with col1:
        cliente = st.text_input("Cliente", key="cliente")
    with col2:
        referencia = st.text_input("Referência", key="referencia")
    with col3:
        id_licitacao = st.text_input("ID", key="id")

    uploaded_files = st.file_uploader(
        "Documentos da Licitação (PDF)",
        type=["txt", "markdown", "mdx", "pdf", "html", "xlsx", "xls", "docx", "csv", "md"],
        accept_multiple_files=True,
        key="docs",
    )

# Submit button outside the form
if uploaded_files:
    submit_disabled = not (cliente and referencia and id_licitacao)
    if st.button(
        "Criar Nova Base de Conhecimento",
        type="primary",
        disabled=submit_disabled,
        use_container_width=True,
    ):
        # TODO: Validate that dataset name is no more than 40 characters long
        dataset_name = f"|{cliente}-{referencia}-{id_licitacao}"

        with st.spinner("Criando base de conhecimento..."):
            try:
                # Create dataset
                dataset_id = dify_client.create_dataset(name=dataset_name)

                # Upload files
                for uploaded_file in uploaded_files:
                    # Create a temporary file
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".pdf"
                    ) as tmp_file:
                        # Write the uploaded file to the temporary file
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file.flush()

                        # Upload to Dify
                        with open(tmp_file.name, "rb") as f:
                            dify_client.upload_knowledge_file(
                                f.read(), uploaded_file.name, dataset_id=dataset_id
                            )

                        # Clean up the temporary file
                        os.unlink(tmp_file.name)

                st.toast("Base de conhecimento criada com sucesso!")
                st.rerun()

            except Exception as e:
                st.error(f"Erro ao criar base de conhecimento: {str(e)}")
else:
    st.info("⬆️ Faça upload dos documentos da licitação para continuar")

st.divider()

# List of existing datasets
st.subheader("Bases de Conhecimento Disponíveis")

try:
    # Fetch all datasets
    datasets = dify_client.fetch_all_datasets()

    if not datasets:
        st.info("Nenhuma base de conhecimento encontrada")
    else:
        for dataset in datasets:
            # Get dataset status
            status_type, status_icon, status_text = dify_client.get_dataset_status(
                dataset["id"]
            )

            # Adjust column widths to minimize spacing between buttons
            col1, col2, col3 = st.columns([0.9, 0.05, 0.05])
            with col1:
                # Extract tender name from dataset name (remove | prefix/suffix)
                tender_name = dataset["name"].replace("|", "").strip()

                with st.expander(
                    f"**Status**: {status_text} {status_icon}     •     **Licitação**: {tender_name}",
                    expanded=False,
                ):
                    # Clean up description text
                    description = f"Útil para buscar informações relevantes referentes à licitação: {tender_name.replace("|", "").strip()}"
                    st.caption(description)
                    st.divider()

                    # List files in dataset
                    files = dify_client.list_dataset_files(dataset["id"])

                    if not files:
                        st.info("Nenhum arquivo encontrado")
                    else:
                        for file in files:
                            status_indicator = (
                                dify_client.get_document_status_indicator(
                                    file.get("indexing_status", "")
                                )
                            )
                            error_msg = file.get("error", "")

                            # Create a container for each document for consistent spacing
                            with st.container():
                                doc_cols = st.columns([0.05, 0.85, 0.1])

                                # Status icon
                                with doc_cols[0]:
                                    st.text(status_indicator)

                                # Document name and error message
                                with doc_cols[1]:
                                    st.text(file["name"])
                                    if error_msg:
                                        st.caption(f"❗ {error_msg}")

                                # Delete button
                                with doc_cols[2]:
                                    if st.button(
                                        "🗑️",
                                        key=f"delete_doc_{dataset['id']}_{file['id']}",
                                        help="Excluir documento",
                                    ):
                                        try:
                                            if dify_client.delete_document(
                                                dataset["id"], file["id"]
                                            ):
                                                st.toast(
                                                    "Documento excluído com sucesso!"
                                                )
                                                st.rerun()
                                        except Exception as e:
                                            st.error(
                                                f"Erro ao excluir documento: {str(e)}"
                                            )

            with col2:
                # Add files button with plus sign icon
                if st.button(
                    "➕",
                    key=f"add_files_{dataset['id']}",
                    help="Adicionar arquivos",
                ):
                    st.session_state.selected_dataset = dataset["id"]
                    st.session_state.show_upload_form = True

            with col3:
                if st.button(
                    "🗑️",
                    key=f"delete_{dataset['id']}",
                    help="Excluir base de conhecimento",
                ):
                    try:
                        if dify_client.delete_dataset(dataset["id"]):
                            st.toast("Base de conhecimento excluída com sucesso!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir base de conhecimento: {str(e)}")

    # Add files form (shown when add_files button is clicked)
    if (
        hasattr(st.session_state, "show_upload_form")
        and st.session_state.show_upload_form
    ):
        st.divider()
        st.subheader("Adicionar Arquivos")

        uploaded_files = st.file_uploader(
            "Selecione os arquivos para adicionar (PDF)",
            type=["pdf"],
            accept_multiple_files=True,
            key="additional_docs",
        )

        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            if uploaded_files:
                if st.button(
                    "Adicionar Arquivos",
                    type="primary",
                    use_container_width=True,
                ):
                    with st.spinner("Adicionando arquivos..."):
                        try:
                            for uploaded_file in uploaded_files:
                                # Create a temporary file
                                with tempfile.NamedTemporaryFile(
                                    delete=False, suffix=".pdf"
                                ) as tmp_file:
                                    # Write the uploaded file to the temporary file
                                    tmp_file.write(uploaded_file.getvalue())
                                    tmp_file.flush()

                                    # Upload to Dify
                                    with open(tmp_file.name, "rb") as f:
                                        dify_client.upload_knowledge_file(
                                            f.read(),
                                            uploaded_file.name,
                                            dataset_id=st.session_state.selected_dataset,
                                        )

                                    # Clean up the temporary file
                                    os.unlink(tmp_file.name)

                            st.toast("Arquivos adicionados com sucesso!")
                            st.session_state.show_upload_form = False
                            st.rerun()

                        except Exception as e:
                            st.error(f"Erro ao adicionar arquivos: {str(e)}")

        with col2:
            if st.button("Cancelar", use_container_width=True):
                st.session_state.show_upload_form = False
                st.rerun()

except Exception as e:
    st.error(f"Erro ao carregar bases de conhecimento: {str(e)}")
