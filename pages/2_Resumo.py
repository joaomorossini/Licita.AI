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
            padding-top: 1.2rem;
            padding-bottom: 1rem;
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

st.title("📋 Resumo de Licitação")
st.divider()

# with st.expander("Documentos da Licitação"):

# File uploader
uploaded_files = st.file_uploader(
    "Faça upload dos documentos da licitação em formato PDF",
    type=["pdf"],
    accept_multiple_files=True,
)

if uploaded_files:
    st.toast(
        f"{len(uploaded_files)} arquivos recebidos para processamento",
        icon="👍",
    )

    st.markdown("### 🔍 Pré-Visualização")
    preview_container = st.container(height=350, border=True)

    try:
        # Process PDFs and store in session state
        st.session_state.tender_documents = utils.load_pdfs_to_docs(uploaded_files)

        if st.session_state.tender_documents:
            # Convert documents to text
            docs_text = utils.concatenate_docs(st.session_state.tender_documents)

            # Display preview of the documents
            with preview_container:
                st.markdown(docs_text)

            # Generate Summary button
            if st.button("Gerar Resumo", type="primary"):
                with st.spinner("Gerando resumo..."):
                    st.session_state.summary = chain.generate_summary(docs_text)

            # Display summary if available
            if st.session_state.summary:
                st.markdown("### 📄 Resumo")
                st.markdown(st.session_state.summary)
        else:
            with preview_container:
                st.markdown(
                    "Faça upload dos documentos para carregar a pré-visualização."
                )
    except Exception as e:
        st.error(f"Erro ao processar os documentos: {str(e)}")
