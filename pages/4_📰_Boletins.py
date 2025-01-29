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
from src.tender_notice_labeling.tender_notice_labeling_template import (
    tender_notice_labeling_template,
    company_business_description,
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

st.title("📰 Processamento de Boletins")
st.divider()

# Initialize session state
if "processed_tenders" not in st.session_state:
    st.session_state.processed_tenders = None
if "processing_status" not in st.session_state:
    st.session_state.processing_status = None
if "error_details" not in st.session_state:
    st.session_state.error_details = None

# Date filters at the top
# st.markdown('<div class="date-filters">', unsafe_allow_html=True)
# date_cols = st.columns([1, 2, 0.5, 1, 2, 6])

# with date_cols[0]:
#     st.markdown('<p class="date-label">De</p>', unsafe_allow_html=True)
# with date_cols[1]:
#     start_date = st.date_input(
#         "De",
#         value=datetime.now().date() - timedelta(days=30),
#         max_value=datetime.now().date(),
#         label_visibility="collapsed",
#     )

# with date_cols[3]:
#     st.markdown('<p class="date-label">Até</p>', unsafe_allow_html=True)
# with date_cols[4]:
#     end_date = st.date_input(
#         "Até",
#         value=datetime.now().date(),
#         max_value=datetime.now().date(),
#         label_visibility="collapsed",
#     )
# st.markdown("</div>", unsafe_allow_html=True)

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

    # # Client filter
    # st.subheader("Cliente")
    # selected_clients = st.multiselect(
    #     "Selecione os clientes",
    #     ["Empresa A", "Empresa B", "Empresa C", "Empresa D", "Empresa E"],
    #     default=[],
    # )

    # # Value range
    # st.subheader("Valor de Referência")
    # min_value = st.number_input(
    #     "Valor mínimo", min_value=0, value=0, step=10000, format="%d"
    # )
    # max_value = st.number_input(
    #     "Valor máximo", min_value=0, value=1000000, step=10000, format="%d"
    # )

    # # Label filter
    # st.subheader("Classificação")
    # selected_labels = st.multiselect(
    #     "Selecione as classificações",
    #     ["Participar", "Talvez", "Não Participar"],
    #     default=[],
    #     help="Filtre as licitações por classificação"
    # )

    # Process button
    st.markdown("---")
    process_button = st.button(
        "⚡ Processar",
        type="primary",
        use_container_width=True,
        disabled=not uploaded_files,
    )

async def process_pdfs(files):
    """Process multiple PDFs asynchronously."""
    try:
        # Initialize Azure OpenAI
        llm = AzureChatOpenAI(
            model="gpt-4o-mini",
            azure_deployment="gpt-4o-mini",
            temperature=0
        )
        
        # Initialize processor
        processor = TenderNoticeProcessor(llm=llm, batch_size=5)
        
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
                        template=tender_notice_labeling_template,
                        company_description=company_business_description,
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
            
            # Map labels to display values with emojis
            label_map = {
                'yes': '✅ Participar',
                'no': '❌ Não participar',
                'unsure': '🤔 Talvez'
            }
            df['label'] = df['label'].map(label_map)
            
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
    relevant = len(st.session_state.processed_tenders[st.session_state.processed_tenders['label'].str.contains('Participar')])
    maybe = len(st.session_state.processed_tenders[st.session_state.processed_tenders['label'].str.contains('Talvez')])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Licitações", total)
    with col2:
        st.metric("Licitações Relevantes", relevant)
    with col3:
        st.metric("Necessitam Análise", maybe)
    
    # Show DataFrame with specific columns and formatting
    display_df = st.session_state.processed_tenders.copy()
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "organization": st.column_config.TextColumn(
                "Cliente",
                help="Nome da organização",
                width="medium",
            ),
            "state": st.column_config.TextColumn(
                "Estado",
                help="Estado",
                width="small",
            ),
            "number": st.column_config.TextColumn(
                "Número",
                help="Número do processo",
                width="small",
            ),
            "object_description": st.column_config.TextColumn(
                "Objeto",
                help="Descrição do objeto",
                width="large",
            ),
            "opening_date": st.column_config.DatetimeColumn(
                "Data",
                help="Data de abertura",
                format="DD/MM/YYYY HH:mm",
                width="medium",
            ),
            "label": st.column_config.TextColumn(
                "Ação",
                help="Ação recomendada para a licitação",
                width="small",
            ),
        },
        column_order=[
            "organization",
            "state",
            "number",
            "object_description",
            "opening_date",
            "label",
        ],
    )
    
    # Download button with semicolon separator
    if st.download_button(
        "📥 Baixar Resultados (CSV)",
        display_df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig'),
        "resultados_licitacoes.csv",
        "text/csv",
        key='download-csv'
    ):
        st.success("Download iniciado!")
