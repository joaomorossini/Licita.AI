from typing import Optional
import streamlit as st
from src.tender_docs_summary_chain import TenderDocsSummaryUtils, TenderDocsSummaryChain

utils = TenderDocsSummaryUtils()
chain = TenderDocsSummaryChain()

# Configure page
st.set_page_config(
    page_title="Resumo de Licitação",
    page_icon="📝",
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
        /* Hide label for date inputs */
        .stDateInput label {
            display: none;
        }
        /* Adjust date input width */
        .stDateInput input {
            width: 100%;
            min-width: 0;
            padding: 0.4rem;
        }
        /* Vertically align date label with input */
        .date-label {
            margin-top: 0.5rem;
            font-weight: 500;
        }
        /* Add spacing after date filters */
        .date-filters {
            margin-bottom: 2rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize session state
if "tender_documents" not in st.session_state:
    st.session_state.tender_documents = None
if "summary" not in st.session_state:
    st.session_state.summary = None
if "docs_text" not in st.session_state:
    st.session_state.docs_text = None

st.title("Resumo de Licitação 📋")
st.divider()

# Sidebar - File Upload Section
with st.sidebar:
    st.markdown("### 📤 Upload de Arquivos")
    uploaded_files = st.file_uploader(
        "Faça upload dos documentos da licitação em formato PDF",
        type=["pdf"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        st.success(f"{len(uploaded_files)} arquivo(s) recebido(s)")

        if st.button("🔄 Carregar", type="primary", use_container_width=True):
            with st.spinner("Processando documentos..."):
                try:
                    # Process PDFs and store in session state
                    st.session_state.tender_documents = utils.load_pdfs_to_docs(
                        uploaded_files
                    )
                    if st.session_state.tender_documents:
                        # Convert documents to text
                        st.session_state.docs_text = utils.concatenate_docs(
                            st.session_state.tender_documents
                        )
                        st.toast("Documentos carregados com sucesso!", icon="✅")
                    else:
                        st.error("Nenhum documento foi processado com sucesso.")
                except Exception as e:
                    st.error(f"Erro ao processar os documentos: {str(e)}")

# Main content area
# Preview section
with st.expander("🔍 Pré-Visualização dos Documentos", expanded=True):
    with st.container(height=400, border=True):
        if st.session_state.get("docs_text"):
            st.markdown(st.session_state.docs_text)
        else:
            st.info("👈 Faça upload dos documentos no painel lateral para começar.")

# Summary section
if st.button(
    "📝 Gerar Resumo",
    type="primary",
    use_container_width=True,
    disabled=not st.session_state.get("docs_text"),
):
    with st.spinner("Gerando resumo..."):
        st.session_state.summary = chain.generate_summary(st.session_state.docs_text)
        st.toast("Resumo gerado com sucesso!", icon="✅")

if st.session_state.summary:
    st.markdown("### 📄 Resumo")
    st.markdown(st.session_state.summary)
