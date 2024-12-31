"""Chat com Edital page."""

import streamlit as st
from src.dify_client import upload_knowledge_file, chat_with_doc

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
            padding-top: 1rem;
            padding-bottom: 0rem;
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

st.title("💬 Assistente de Licitações")

# Define supported file types
SUPPORTED_TYPES = [
    "txt",
    "md",
    "markdown",
    "pdf",
    "html",
    "htm",
    "xlsx",
    "xls",
    "docx",
    "csv",
]
MAX_FILE_SIZE_MB = 15

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "doc_id" not in st.session_state:
    st.session_state.doc_id = None
if "upload_status" not in st.session_state:
    st.session_state.upload_status = None
if "search_query" not in st.session_state:
    st.session_state.search_query = ""

# Sidebar with document list
with st.sidebar:
    # Add search box after navigation
    search = st.text_input(
        "",
        value=st.session_state.search_query,
        placeholder="🔍 Buscar",
    )
    if search != st.session_state.search_query:
        st.session_state.search_query = search
    st.markdown("---")  # Second divider

    st.title("Histórico")
    if st.session_state.doc_id:
        st.success("Documento atual carregado")
        st.caption(f"ID do documento: {st.session_state.doc_id}")

    # Filter editais based on search query
    editais = [f"Licitação {chr(65 + i)}" for i in range(7)]

    if search:
        editais = [e for e in editais if search.lower() in e.lower()]

    if not editais:
        st.info("Nenhum edital encontrado")
    else:
        for edital in editais:
            st.write(edital)

# Main content area
with st.container():
    with st.container(height=450, border=True):
        # Welcome message (only shown when no messages exist)
        if not st.session_state.messages:
            with st.chat_message("assistant"):
                st.write("👋 Olá! Sou seu assistente de IA")

        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Chat input - Will be automatically pinned to bottom
    if prompt := st.chat_input("Converse com o assistente..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display updated chat history immediately
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                try:
                    response_placeholder = st.empty()
                    full_response = []

                    # Stream the response
                    for response_chunk in chat_with_doc(
                        st.session_state.doc_id, prompt
                    ):
                        if response_chunk:
                            full_response.append(response_chunk)
                            # Display intermediate response
                            response_placeholder.markdown("".join(full_response) + "▌")

                    # Display final response
                    final_response = "".join(full_response)
                    if final_response:
                        response_placeholder.markdown(final_response)
                        # Add to message history
                        st.session_state.messages.append(
                            {"role": "assistant", "content": final_response}
                        )
                    else:
                        response_placeholder.markdown(
                            "❌ Nenhuma resposta recebida do assistente"
                        )
                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": "❌ Nenhuma resposta recebida do assistente",
                            }
                        )

                except Exception as e:
                    error_msg = f"❌ Erro: {str(e)}"
                    response_placeholder.markdown(error_msg)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": error_msg}
                    )

        st.rerun()

    # Document handling section
    doc_container = st.container()
    with doc_container:
        # File upload section
        uploaded_file = st.file_uploader(
            "Enviar Documento",
            type=SUPPORTED_TYPES,
            help=f"Formatos suportados: {', '.join(SUPPORTED_TYPES).upper()} • Tamanho máximo: {MAX_FILE_SIZE_MB}MB",
        )

        if uploaded_file and st.session_state.upload_status != uploaded_file.name:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            if file_size_mb > MAX_FILE_SIZE_MB:
                st.error(
                    f"❌ Arquivo muito grande! Tamanho máximo é {MAX_FILE_SIZE_MB}MB. Seu arquivo tem {file_size_mb:.1f}MB"
                )
            else:
                try:
                    with st.spinner("Enviando documento..."):
                        doc_id = upload_knowledge_file(
                            uploaded_file.getvalue(), uploaded_file.name
                        )
                        st.session_state.doc_id = doc_id
                        st.session_state.upload_status = uploaded_file.name
                        st.success("✅ Documento enviado com sucesso!")
                        st.info(
                            "⏳ O documento está sendo processado. Você já pode começar a fazer perguntas enquanto ele é analisado."
                        )
                except Exception as e:
                    st.error(f"❌ Erro ao enviar documento: {str(e)}")
