from typing import Optional
import streamlit as st
import rootpath

rootpath.append()

# TODO: Tix this import
from src.tender_analysis_crew.crew import TenderAnalysisCrew, TenderAnalysisUtils

# TODO: Otimizar formato e instruções do resumo com base nos resumos da Fast
# TODO: Adicionar opção para salvar resumo em PDF
# TODO: Utilizar API da Adobe pra ler pdfs complexos, contendo imagens e tabelas: https://opensource.adobe.com/developers.adobe.com/apis/documentcloud/dcsdk/pdf-extract.html

crew = TenderAnalysisCrew()
utils = TenderAnalysisUtils()

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
if "tender_pdfs" not in st.session_state:
    st.session_state.tender_pdfs = None
if "tender_documents_text" not in st.session_state:
    st.session_state.tender_documents_text = None
if "summary" not in st.session_state:
    st.session_state.summary = None

st.title("Resumo de Licitação (CrewAI gpt-4o) 📋")
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

        if st.button("⬆️ Carregar", type="primary", use_container_width=True):
            st.session_state.summary = None
            with st.spinner("Carregando documentos..."):
                try:
                    # Load PDFs and store in session state
                    st.session_state.tender_pdfs = utils.load_pdfs_to_docs(
                        uploaded_files
                    )
                    if st.session_state.tender_pdfs:
                        # Convert documents to text
                        st.session_state.tender_documents_text = utils.concatenate_docs(
                            st.session_state.tender_pdfs
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
        if st.session_state.get("tender_documents_text"):
            st.markdown(st.session_state.tender_documents_text)
        else:
            st.info("👈 Faça upload dos documentos no painel lateral para começar.")

# Summary section
if st.button(
    "📝 Gerar Resumo",
    type="primary",
    use_container_width=True,
    disabled=not st.session_state.get("tender_documents_text"),
):
    with st.spinner("Gerando resumo..."):
        st.session_state.summary = crew.generate_summary(
            st.session_state.tender_documents_text
        )
        st.toast("Resumo gerado com sucesso!", icon="✅")

if st.session_state.summary:
    st.markdown("### 📄 Resumo")
    st.markdown(st.session_state.summary)
