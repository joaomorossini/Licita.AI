import os
import requests
import streamlit as st
from dotenv import load_dotenv
import json

from src.dify_client import DifyClient

load_dotenv()

# Initialize Dify client
dify_client = DifyClient()

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
            padding-top: 1.5rem;
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
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "doc_id" not in st.session_state:
    st.session_state.doc_id = None
if "upload_status" not in st.session_state:
    st.session_state.upload_status = None
if "search_query" not in st.session_state:
    st.session_state.search_query = ""

# Sidebar
with st.sidebar:
    # Add search box after navigation
    search = st.text_input(
        "Buscar",
        value=st.session_state.search_query,
        placeholder="🔍 Buscar",
        label_visibility="collapsed",
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


st.title("💬 Assistente de Licitações")

# Display chat message history from session state
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Get user input
prompt = st.chat_input("Enter you question")

if prompt:
    # Display and store user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Handle assistant's response
    with st.chat_message("assistant"):
        # Create placeholder for streaming response
        message_placeholder = st.empty()
        full_response = ""

        try:
            # Stream response from Dify API
            # IMPORTANT: This maintains both streaming output and conversation history
            for (
                message_content,
                conversation_id,
                is_end,
            ) in dify_client.stream_dify_response(
                st.session_state.conversation_id, prompt
            ):
                # Update streaming message in real-time
                if message_content:
                    full_response += message_content
                    message_placeholder.markdown(full_response)
                # Store final response and update conversation ID
                if is_end and conversation_id:
                    st.session_state.conversation_id = conversation_id
                    st.session_state.messages.append(
                        {"role": "assistant", "content": full_response}
                    )

        except Exception as e:
            # Handle errors while maintaining conversation flow
            st.error(f"Request error: {str(e)}")
            full_response = "An error occurred while making the request."
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )

    # # TODO: Handle knowledge base updates
    # doc_container = st.container()
    # with doc_container:
    #     # File upload section
    #     uploaded_file = st.file_uploader(
    #         "Enviar Documento",
    #         type=SUPPORTED_TYPES,
    #         help=f"Formatos suportados: {', '.join(SUPPORTED_TYPES).upper()} • Tamanho máximo: {MAX_FILE_SIZE_MB}MB",
    #     )

    #     if uploaded_file and st.session_state.upload_status != uploaded_file.name:
    #         file_size_mb = uploaded_file.size / (1024 * 1024)
    #         if file_size_mb > MAX_FILE_SIZE_MB:
    #             st.error(
    #                 f"❌ Arquivo muito grande! Tamanho máximo é {MAX_FILE_SIZE_MB}MB. Seu arquivo tem {file_size_mb:.1f}MB"
    #             )
    #         else:
    #             try:
    #                 with st.spinner("Enviando documento..."):
    #                     doc_id = dify_client.upload_knowledge_file(
    #                         uploaded_file.getvalue(), uploaded_file.name
    #                     )
    #                     st.session_state.doc_id = doc_id
    #                     st.session_state.upload_status = uploaded_file.name
    #                     st.success("✅ Documento enviado com sucesso!")
    #                     st.info(
    #                         "⏳ O documento está sendo processado. Você já pode começar a fazer perguntas enquanto ele é analisado."
    #                     )
    #             except Exception as e:
    #                 st.error(f"❌ Erro ao enviar documento: {str(e)}")
