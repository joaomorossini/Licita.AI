import os
import requests
import streamlit as st
from dotenv import load_dotenv
import json
from st_multimodal_chatinput import multimodal_chatinput

from src.dify_client import upload_knowledge_file

load_dotenv()

dify_api_key = os.getenv("DIFY_API_KEY")

url = "http://dify.cogmo.com.br/v1/chat-messages"

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


st.title("💬 Assistente de Licitações")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

chat_input = multimodal_chatinput()

if chat_input is not None and (
    chat_input.get("textInput") or chat_input.get("uploadedFiles")
):
    prompt = chat_input.get("textInput", "")
    files = chat_input.get("uploadedFiles", [])

    # Display user message
    with st.chat_message("user"):
        if prompt:
            st.markdown(prompt)
        for file in files:
            st.markdown(f"📎 Arquivo enviado: {file['name']}")

    # Add to message history
    content = []
    if prompt:
        content.append(prompt)
    if files:
        content.append("\n".join([f"📎 {file['name']}" for file in files]))
    st.session_state.messages.append({"role": "user", "content": "\n".join(content)})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        headers = {
            "Authorization": f"Bearer {dify_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "inputs": {},
            "query": prompt if prompt else "Analise o arquivo anexado.",
            "response_mode": "streaming",
            "conversation_id": st.session_state.conversation_id,
            "user": "aianytime",
            "files": [],
        }

        try:
            with requests.post(
                url, headers=headers, json=payload, stream=True
            ) as response:
                response.raise_for_status()
                full_response = ""

                for line in response.iter_lines():
                    if line:
                        line = line.decode("utf-8")
                        if line.startswith("data: "):
                            try:
                                event_data = json.loads(
                                    line[6:]
                                )  # Skip 'data: ' prefix
                                if event_data.get("event") == "agent_message":
                                    message_content = event_data.get("answer", "")
                                    if message_content:
                                        full_response += message_content
                                        message_placeholder.markdown(full_response)
                                elif event_data.get("event") == "message_end":
                                    st.session_state.conversation_id = event_data.get(
                                        "conversation_id",
                                        st.session_state.conversation_id,
                                    )
                            except json.JSONDecodeError:
                                continue

        except requests.exceptions.RequestException as e:
            st.error(f"Request error: {str(e)}")
            full_response = "An error occurred while making the request."

        message_placeholder.markdown(full_response)
        if full_response:  # Only append if we got a response
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )

    # # Document handling section
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
    #                     doc_id = upload_knowledge_file(
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
