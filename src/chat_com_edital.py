"""Chat com Edital interface module."""

import streamlit as st
from src.dify_client import upload_knowledge_file, chat_with_doc

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


def chat_com_edital_page():
    """Display the Chat com Edital page with file upload and chat functionality."""

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "doc_id" not in st.session_state:
        st.session_state.doc_id = None
    if "upload_status" not in st.session_state:
        st.session_state.upload_status = None

    # Sidebar
    with st.sidebar:
        st.title("Licitações")
        if st.session_state.doc_id:
            st.success("Documento atual carregado")
            st.caption(f"ID do documento: {st.session_state.doc_id}")

        # Example document list
        for i in range(7):
            st.write(f"Edital {chr(65 + i)}")
        st.write("...")
        st.write("Edital Z")

    # Main content area
    st.title("💬 Assistente de Licitações")

    # Chat messages container
    chat_container = st.container()

    # File upload and I/O container
    file_container = st.container()

    # Display chat interface in the chat container
    with chat_container:
        # Welcome message (only shown when no messages exist)
        if not st.session_state.messages:
            st.info("👋 Olá! Sou seu assistente de IA. Estou aqui para ajudar.")

        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Handle file upload and I/O in the file container
    with file_container:
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
                return False

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
                return False

        # Input/Output Files tabs
        tab1, tab2 = st.tabs(["Arquivos de Entrada", "Arquivos de Saída"])
        with tab1:
            st.write("Os arquivos de entrada serão listados aqui")
        with tab2:
            st.write("Os arquivos gerados aparecerão aqui")

    # Chat input - This should be the last element
    if prompt := st.chat_input("Converse com o assistente..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get and display assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = []

            try:
                for response_chunk in chat_with_doc(st.session_state.doc_id, prompt):
                    if response_chunk:
                        full_response.append(response_chunk)
                        message_placeholder.markdown("".join(full_response))

                final_response = "".join(full_response)
                if final_response:
                    st.session_state.messages.append(
                        {"role": "assistant", "content": final_response}
                    )
                else:
                    message_placeholder.error(
                        "❌ Nenhuma resposta recebida do assistente"
                    )

            except Exception as e:
                error_msg = f"❌ Erro: {str(e)}"
                message_placeholder.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )
                st.error(f"Erro detalhado: {str(e)}")

    return True
