from typing import Optional
import streamlit as st
import rootpath
import asyncio
import os
import logging
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

rootpath.append()

from src.tender_analysis_crew.crew import TenderAnalysisCrew, TenderAnalysisUtils

# TO-DO
## TODO: Adicionar botão para download do resumo em PDF
## TODO: Adicionar botão para adicionar resumo a uma base de conhecimento existente ou criar uma nova

# SOMEDAY MAYBE
## TODO: Utilizar API da Adobe pra ler pdfs complexos, contendo imagens e tabelas: https://opensource.adobe.com/developers.adobe.com/apis/documentcloud/dcsdk/pdf-extract.html

crew = TenderAnalysisCrew()
utils = TenderAnalysisUtils()
logger = logging.getLogger(__name__)

def markdown_to_pdf(markdown_text: str | object) -> BytesIO:
    """Convert markdown text to PDF.
    
    Args:
        markdown_text: The markdown text to convert (can be string or CrewOutput object)
        
    Returns:
        BytesIO: PDF file as bytes
    """
    # Convert to string if needed
    text_content = str(markdown_text)
    
    # Create a BytesIO buffer to receive PDF data
    buffer = BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    
    # Create custom style for better readability
    custom_style = ParagraphStyle(
        'CustomStyle',
        parent=normal_style,
        spaceBefore=10,
        spaceAfter=10,
        leading=14,
    )
    
    # Convert markdown to PDF elements
    elements = []
    
    # Split text into paragraphs and process each
    paragraphs = text_content.split('\n')
    for paragraph in paragraphs:
        if paragraph.strip():  # Skip empty lines
            # Clean up any XML-unsafe characters
            cleaned_text = (
                paragraph.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
            )
            p = Paragraph(cleaned_text, custom_style)
            elements.append(p)
            elements.append(Spacer(1, 0.1 * inch))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

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
if "labeled_sections" not in st.session_state:
    st.session_state.labeled_sections = None
if "filtered_sections" not in st.session_state:
    st.session_state.filtered_sections = None
if "summary" not in st.session_state:
    st.session_state.summary = ""
if "show_preview" not in st.session_state:
    st.session_state.show_preview = True
if "processing_status" not in st.session_state:
    st.session_state.processing_status = None
if "error_details" not in st.session_state:
    st.session_state.error_details = None

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

        if st.button("⬆️ Carregar", type="primary", use_container_width=True):
            # Reset all states
            st.session_state.summary = None
            st.session_state.labeled_sections = None
            st.session_state.filtered_sections = None
            st.session_state.processing_status = None
            st.session_state.error_details = None
            
            with st.spinner("Carregando documentos..."):
                try:
                    # Load PDFs and store in session state
                    st.session_state.tender_pdfs = utils.load_pdfs_to_docs(uploaded_files)
                    
                    if st.session_state.tender_pdfs:
                        # Convert documents to text
                        st.session_state.tender_documents_text = utils.concatenate_docs(
                            st.session_state.tender_pdfs
                        )
                        st.toast("Documentos carregados com sucesso!", icon="✅")
                    else:
                        st.error("Nenhum documento foi processado com sucesso.")
                        logger.error("No documents were successfully processed")
                except Exception as e:
                    error_msg = f"Erro ao processar os documentos: {str(e)}"
                    st.error(error_msg)
                    logger.error(error_msg, exc_info=True)
                    st.session_state.error_details = str(e)

# Main content area
# Preview section
with st.expander("🔍 Pré-Visualização dos Documentos", expanded=st.session_state.show_preview):
    with st.container(height=400, border=True):
        if st.session_state.get("tender_documents_text"):
            try:
                # Add text length information
                total_chars = len(st.session_state.tender_documents_text)
                total_tokens = utils._length_function(st.session_state.tender_documents_text)
                chunks = utils.split_text(st.session_state.tender_documents_text)
                st.caption(
                    f"📊 Estatísticas do Documento: {total_chars:,} caracteres • {total_tokens} tokens • {len(chunks)} partes"
                )
                st.markdown(st.session_state.tender_documents_text)
            except Exception as e:
                error_msg = f"Erro ao exibir pré-visualização: {str(e)}"
                st.error(error_msg)
                logger.error(error_msg, exc_info=True)
        else:
            st.info("👈 Faça upload dos documentos no painel lateral para começar.")

# Summary section
if st.button(
    "📝 Gerar Resumo",
    type="primary",
    use_container_width=True,
    disabled=not st.session_state.get("tender_documents_text"),
):
    # Reset error state
    st.session_state.error_details = None
    
    # Create a placeholder for the progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()

    with st.spinner("Gerando resumo..."):
        try:
            # Get total number of chunks for progress calculation
            chunks = utils.split_text(st.session_state.tender_documents_text)
            total_chunks = len(chunks)

            # Update initial status
            st.session_state.processing_status = f"Processando parte 0/{total_chunks}"
            status_text.text(st.session_state.processing_status)

            def update_progress(current_chunk: int):
                """Update progress bar and status text"""
                try:
                    progress = float(current_chunk) / total_chunks
                    progress_bar.progress(progress)
                    st.session_state.processing_status = (
                        f"Processando parte {current_chunk}/{total_chunks}"
                    )
                    status_text.text(st.session_state.processing_status)
                except Exception as e:
                    logger.error(f"Error updating progress: {str(e)}", exc_info=True)

            # Generate summary with progress updates
            st.session_state.summary = asyncio.run(
                crew.generate_summary(
                    st.session_state.tender_documents_text,
                    progress_callback=update_progress,
                )
            )

            # Update final status
            progress_bar.progress(1.0)
            status_text.text("Resumo gerado com sucesso!")
            st.session_state.show_preview = False
            st.toast("Resumo gerado com sucesso!", icon="✅")

        except Exception as e:
            error_msg = f"Erro ao gerar resumo: {str(e)}"
            st.error(error_msg)
            logger.error(error_msg, exc_info=True)
            st.session_state.error_details = str(e)
        finally:
            # Clean up progress display
            progress_bar.empty()
            status_text.empty()

if st.session_state.summary:
    st.markdown(st.session_state.summary)
    
    # Add download button
    pdf_buffer = markdown_to_pdf(st.session_state.summary)
    st.download_button(
        label="⬇️ Baixar PDF",
        data=pdf_buffer,
        file_name="resumo_licitacao.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )

# Display detailed error information if available
if st.session_state.error_details and os.getenv("ENVIRONMENT") == "dev":
    with st.expander("🐛 Detalhes do Erro"):
        st.code(st.session_state.error_details)
