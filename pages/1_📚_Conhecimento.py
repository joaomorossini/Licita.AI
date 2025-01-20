import streamlit as st
import asyncio
from typing import Dict, List
import tempfile

from src.tender_knowledge import TenderKnowledge, DocumentProcessingStatus

# Initialize client
knowledge = TenderKnowledge()

# Page config
st.set_page_config(page_title="Conhecimento", page_icon="📄", layout="wide")

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

# Initialize session state
if "processing_status" not in st.session_state:
    st.session_state.processing_status = {}
if "show_upload_form" not in st.session_state:
    st.session_state.show_upload_form = False
if "selected_index" not in st.session_state:
    st.session_state.selected_index = None

with st.sidebar:
    st.info(
        """⚠️ **ATENÇÃO**: Fique atento ao **status de processamento** dos seus arquivos. 
        Caso note que algum documento está demorando muito para processar, você pode deletá-lo e adicioná-lo novamente.""",
    )

# Title
st.title("Conhecimento 📚")
st.divider()


# Function to get status icon and color
def get_status_display(status: str) -> tuple:
    """Get status icon and color for display."""
    if status == "pending":
        return "⏳", "gray", "Pendente"
    elif status == "processing":
        return "🔄", "blue", "Processando"
    elif status == "generating_embeddings":
        return "🧠", "orange", "Gerando embeddings"
    elif status == "completed":
        return "✅", "green", "Concluído"
    elif status == "error":
        return "❌", "red", "Erro"
    return "❓", "gray", "Desconhecido"


# Function to update status in session state
def update_status(status: DocumentProcessingStatus):
    """Update document status in session state."""
    if status.filename not in st.session_state.processing_status:
        st.session_state.processing_status[status.filename] = {}

    st.session_state.processing_status[status.filename].update(
        {
            "status": status.status,
            "total_pages": status.total_pages,
            "processed_pages": status.processed_pages,
            "total_chunks": status.total_chunks,
            "processed_chunks": status.processed_chunks,
            "error": status.error,
        }
    )


# Create new knowledge base section
st.subheader("Criar Nova Base de Conhecimento")

# Check number of existing indexes
existing_indexes = knowledge.client.list_indexes()
if len(existing_indexes) >= 5:
    st.warning(
        """⚠️ **Limite de bases de conhecimento atingido!**
        
        Você já possui 5 bases de conhecimento. Para criar uma nova, você precisará excluir uma das bases existentes.""",
        icon="⚠️",
    )

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
        type=["pdf"],
        accept_multiple_files=True,
        key="docs",
    )

# Submit button outside the form
if uploaded_files:
    submit_disabled = (
        not (cliente and referencia and id_licitacao) or len(existing_indexes) >= 5
    )
    if st.button(
        "Criar Nova Base de Conhecimento",
        type="primary",
        disabled=submit_disabled,
        use_container_width=True,
    ):
        # Format index name to be valid (lowercase, alphanumeric, hyphens)
        formatted_name = f"{cliente}-{referencia}-{id_licitacao}".lower()
        formatted_name = "".join(
            c if c.isalnum() or c == "-" else "-" for c in formatted_name
        )
        formatted_name = "-".join(
            filter(None, formatted_name.split("-"))
        )  # Remove empty segments

        with st.spinner("Criando base de conhecimento..."):
            try:
                # Process documents
                statuses = asyncio.run(
                    knowledge.process_tender_documents(
                        index_name=formatted_name,
                        uploaded_files=uploaded_files,
                        status_callback=update_status,
                    )
                )

                # Check for any errors
                if any(s.status == "error" for s in statuses):
                    error_docs = [s.filename for s in statuses if s.status == "error"]
                    st.error(
                        f"Erro ao processar os seguintes documentos: {', '.join(error_docs)}"
                    )
                else:
                    st.success("Base de conhecimento criada com sucesso!")
                    st.rerun()

            except Exception as e:
                st.error(f"Erro ao criar base de conhecimento: {str(e)}")
else:
    st.info("⬆️ Faça upload dos documentos da licitação para continuar")

st.divider()

# List of existing knowledge bases
st.subheader("Bases de Conhecimento")

try:
    # Fetch all indexes
    indexes = knowledge.client.list_indexes()

    if not indexes:
        st.info("Nenhuma base de conhecimento encontrada")
    else:
        for index_name in indexes:
            try:
                # Get namespaces (documents) in this index
                namespaces = knowledge.client.list_namespaces(index_name)

                # Adjust column widths to minimize spacing between buttons
                col1, col2, col3 = st.columns([0.9, 0.05, 0.05])
                with col1:
                    with st.expander(f"**{index_name}**", expanded=False):
                        if not namespaces:
                            st.info("Nenhum documento encontrado")
                        else:
                            for namespace in namespaces:
                                # Get status from session state or default to completed
                                doc_status = st.session_state.processing_status.get(
                                    f"{namespace}.pdf", {"status": "completed"}
                                )
                                status_icon, status_color, status_text = (
                                    get_status_display(doc_status["status"])
                                )

                                # Create a container for each document
                                with st.container():
                                    doc_cols = st.columns([0.05, 0.85, 0.1])

                                    # Status icon
                                    with doc_cols[0]:
                                        st.markdown(
                                            f":{status_color}[{status_icon}]",
                                            unsafe_allow_html=True,
                                        )

                                    # Document name and status
                                    with doc_cols[1]:
                                        st.text(f"{namespace}.pdf")
                                        if doc_status["status"] == "error":
                                            st.caption(f"❗ {doc_status['error']}")
                                        elif doc_status["status"] in [
                                            "processing",
                                            "generating_embeddings",
                                        ]:
                                            progress = 0
                                            if doc_status["status"] == "processing":
                                                progress = (
                                                    doc_status["processed_pages"]
                                                    / doc_status["total_pages"]
                                                )
                                            else:
                                                progress = (
                                                    doc_status["processed_chunks"]
                                                    / doc_status["total_chunks"]
                                                )
                                            st.progress(progress, text=status_text)

                                    # Delete button
                                    with doc_cols[2]:
                                        if st.button(
                                            "🗑️",
                                            key=f"delete_doc_{index_name}_{namespace}",
                                            help="Excluir documento",
                                        ):
                                            try:
                                                if knowledge.client.delete_namespace(
                                                    index_name, namespace
                                                ):
                                                    st.success(
                                                        "Documento excluído com sucesso!"
                                                    )
                                                    st.rerun()
                                            except Exception as e:
                                                st.error(
                                                    f"Erro ao excluir documento: {str(e)}"
                                                )

                with col2:
                    # Add files button
                    if st.button(
                        "➕",
                        key=f"add_files_{index_name}",
                        help="Adicionar arquivos",
                    ):
                        st.session_state.selected_index = index_name
                        st.session_state.show_upload_form = True

                with col3:
                    # Delete index button
                    if st.button(
                        "🗑️",
                        key=f"delete_{index_name}",
                        help="Excluir base de conhecimento",
                    ):
                        try:
                            if knowledge.client.delete_index(index_name):
                                st.success("Base de conhecimento excluída com sucesso!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao excluir base de conhecimento: {str(e)}")

            except Exception as e:
                st.error(f"Erro ao carregar documentos da base {index_name}: {str(e)}")
                continue

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
                            # Process documents
                            statuses = asyncio.run(
                                knowledge.process_tender_documents(
                                    index_name=st.session_state.selected_index,
                                    uploaded_files=uploaded_files,
                                    status_callback=update_status,
                                )
                            )

                            # Check for any errors
                            if any(s.status == "error" for s in statuses):
                                error_docs = [
                                    s.filename for s in statuses if s.status == "error"
                                ]
                                st.error(
                                    f"Erro ao processar os seguintes documentos: {', '.join(error_docs)}"
                                )
                            else:
                                st.success("Arquivos adicionados com sucesso!")
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
