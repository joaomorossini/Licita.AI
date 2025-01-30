"""Boletins page."""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import tempfile
import os
from langchain_community.chat_models import AzureChatOpenAI
import io
import asyncio
from tempfile import NamedTemporaryFile

from src.tender_notice_labeling.tender_notice_processor import TenderNoticeProcessor
from src.tender_notice_labeling.tender_notice_templates import (
    TENDER_NOTICE_LABELING_TEMPLATE,
    COMPANY_BUSINESS_DESCRIPTION,
)

# Configure page
st.set_page_config(
    page_title="Boletins - Licita.AI",
    page_icon="📰",
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
        /* Style for tender labels */
        .label-yes {
            color: #00cc00;
            font-weight: bold;
        }
        .label-no {
            color: #ff0000;
            font-weight: bold;
        }
        .label-unsure {
            color: #ffa500;
            font-weight: bold;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📰 Boletins de Licitações")
st.divider()

# Initialize session state
if "processed_tenders" not in st.session_state:
    st.session_state.processed_tenders = None
if "processing_status" not in st.session_state:
    st.session_state.processing_status = None
if "error_details" not in st.session_state:
    st.session_state.error_details = None


# Filters in sidebar
with st.sidebar:
    st.markdown(
        """
        <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
        <h1 style="display: flex; align-items: center;">
            Filtros&nbsp<span class="material-icons">filter_alt</span>
        </h1>
        """,
        unsafe_allow_html=True,
    )

    # File upload section
    st.markdown("### 📤 Upload de Arquivos")
    uploaded_files = st.file_uploader(
        "Selecione os boletins para processar (PDF)",
        type=['pdf'],
        accept_multiple_files=True
    )

    if uploaded_files:
        st.success(f"{len(uploaded_files)} arquivo(s) recebido(s)")

    # Process button
    st.markdown("---")
    process_button = st.button(
        "⚡ Processar",
        type="primary",
        use_container_width=True,
        disabled=not uploaded_files,
    )

# TODO: Refactor. Move to src/tender_notice_labeling/tender_notice_processor.py
async def process_pdfs(files):
    """Process multiple PDFs asynchronously."""
    try:
        # Initialize processor with correct model settings
        processor = TenderNoticeProcessor()
        
        # Process each PDF
        all_tenders = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, file in enumerate(files):
            try:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(file.getvalue())
                    tmp_path = tmp_file.name
                
                try:
                    # Update status
                    status_text.text(f"Processando {file.name}...")
                    
                    # Process PDF
                    df = await processor.process_pdf(
                        pdf_path=tmp_path,
                        template=TENDER_NOTICE_LABELING_TEMPLATE,
                        company_description=COMPANY_BUSINESS_DESCRIPTION,
                        max_concurrent_chunks=5
                    )
                    
                    if not df.empty:
                        # Add source information
                        df['source_file'] = file.name
                        df['processed_at'] = datetime.now()
                        all_tenders.append(df)
                    
                finally:
                    # Clean up temp file
                    os.unlink(tmp_path)
                
            except Exception as e:
                st.error(f"Erro ao processar {file.name}: {str(e)}")
                if os.getenv("ENVIRONMENT") == "dev":
                    st.exception(e)
                continue
            
            # Update progress
            progress = (i + 1) / len(files)
            progress_bar.progress(progress)
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        # Combine all results
        if all_tenders:
            df = pd.concat(all_tenders, ignore_index=True)
            return df
            
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"Erro ao processar os boletins: {str(e)}")
        if os.getenv("ENVIRONMENT") == "dev":
            st.exception(e)
        return pd.DataFrame()

# Main content area
if process_button and uploaded_files:
    with st.spinner("Processando boletins..."):
        # Run async processing
        st.session_state.processed_tenders = asyncio.run(process_pdfs(uploaded_files))
        
        if not st.session_state.processed_tenders.empty:
            st.toast("Processamento concluído com sucesso!", icon="✅")
        else:
            st.error("Nenhum boletim foi processado com sucesso.")
                
# Display results
if st.session_state.processed_tenders is not None and not st.session_state.processed_tenders.empty:
    # Display statistics
    total = len(st.session_state.processed_tenders)
    
    # Safe label counting
    def count_labels(df: pd.DataFrame, pattern: str) -> int:
        return df['label'].str.contains(pattern, na=False).sum()
    
    relevant = count_labels(st.session_state.processed_tenders, 'Participar')
    need_analysis = count_labels(st.session_state.processed_tenders, 'Avaliar')
    irrelevant = total - relevant - need_analysis
    
    st.markdown(
        """
        <style>
            .metric-label {
                font-size: 20px;
                text-align: center;
            }
            .metric-value {
                font-size: 50px;
                text-align: center;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-label">TOTAL DE BOLETINS</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{total}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-label">PARTICIPAR</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{relevant}</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-label">AVALIAR</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{need_analysis}</div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="metric-label">DECLINAR</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{irrelevant}</div>', unsafe_allow_html=True)
    
    # Show DataFrame with specific columns and formatting
    display_df = st.session_state.processed_tenders.copy()
    
    # Ensure all columns have proper values
    display_df['orgao'] = display_df['orgao'].fillna('Organização não identificada')
    display_df['estado'] = display_df['estado'].fillna('N/A')
    display_df['numero_licitacao'] = display_df['numero_licitacao'].fillna('N/A')
    display_df['objeto'] = display_df['objeto'].fillna('Descrição não disponível')
    
    st.dataframe(
        data=display_df,
        height=400,
        use_container_width=True,
        hide_index=True,
        column_config={
            "orgao": st.column_config.TextColumn(
                "Cliente",
                help="Nome da organização",
                width="medium",
            ),
            "estado": st.column_config.TextColumn(
                "UF",
                help="UF",
                width="small",
            ),
            "numero_licitacao": st.column_config.TextColumn(
                "Nº",
                help="Número do processo",
                width="small",
            ),
            "objeto": st.column_config.TextColumn(
                "Descrição do objeto",
                help="Descrição do objeto",
                width="large",
            ),
            "data_hora_licitacao": st.column_config.DatetimeColumn(
                "Data",
                help="Data de abertura",
                format="DD/MM/YYYY HH:mm",
                width="medium",
            ),
            "label": st.column_config.TextColumn(
                "Recomendação",
                help="Ação recomendada para a licitação",
                width="small",
            ),
        },
        column_order=[
            "orgao",
            "estado",
            "numero_licitacao",
            "objeto",
            "data_hora_licitacao",
            "label",
        ],
    )
    
    # Download buttons
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        # CSV download button
        if st.download_button(
            "📥 Baixar Resultados (CSV)",
            display_df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig'),
            "resultados_licitacoes.csv",
            "text/csv",
            key='download-csv'
        ):
            st.toast("Download iniciado!")
    
    with col2:
        # Excel download button
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            display_df.to_excel(writer, index=False, sheet_name='Licitações')
        
        if st.download_button(
            "📥 Baixar Resultados (Excel)",
            excel_buffer.getvalue(),
            "resultados_licitacoes.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key='download-excel'
        ):
            st.toast("Download iniciado!")
