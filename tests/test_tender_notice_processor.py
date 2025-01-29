import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, mock_open
from langchain_core.messages import AIMessage
from langchain_core.documents import Document
from src.tender_notice_labeling.tender_notice_processor import TenderNoticeProcessor, TenderNotice
import logging
import os
import mimetypes
import tempfile

# Initialize mimetypes without reading system files
mimetypes.init()
mimetypes.add_type('application/pdf', '.pdf')

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

SAMPLE_TENDER_BLOCK = """SAAE / DAE / SAMAE - Serviços Autônomos de Água e Esgoto do Municipio (1/29)
Licitações Novas
Tipo de Órgão:Municipal Cidade: Aracruz ES
Modalidade: CONCORRÊNCIA PÚBLICA ELETRÔNICA Nº: 6/2024
Objeto:
Contratação de empresa para fornecimento e instalação de sistema de vídeo
monitoramento digital baseado em câmeras de tecnologia ip, para a estação de
tratamento de esgoto - ete sul e usina fotovoltaica
Segmentação: Seguranca Eletronica - CFTV, SSTV
Abertura: 21/11/2024 09:00 ID Universo: 10224184
Telefone: (27) 3256-9409 Telefone 2:
Acesso:
http://www.saaeara.com.br
licitacao@saaeara.com.br
Complementos:
Fonte Diário dos Municipios"""

SAMPLE_EMAIL_TEXT = f"""Relatório de Licitações Públicas
//////////////// 
Total de licitações encontradas: 29
Novas: 25
Alteradas / Retificadas: 4

{SAMPLE_TENDER_BLOCK}

COPASA - Cia de Saneamento de Minas Gerais (2/29)
Tipo de Órgão:Estatal Cidade: Belo Horizonte MG
Modalidade: LEI DAS ESTATAIS Nº: 820246978
Objeto: Material para estacoes de tratamento - grjb
Segmentação: Construcao Civil - Material diversos
Abertura: 04/11/2024 20:59 ID Universo: 10224212
Telefone: (31) 3250-1165 Telefone 2: (31) 3250-1690
Acesso:
http://www.copasa.com.br
dvlcac@copasa.com.br
Complementos:Fonte Captação Interna"""

@pytest.fixture
def mock_llm():
    mock = MagicMock()
    mock.invoke.return_value = AIMessage(content="yes")
    return mock

@pytest.fixture
def processor(mock_llm):
    return TenderNoticeProcessor(llm=mock_llm)

def test_extract_tender_blocks(processor):
    blocks = processor._extract_tender_blocks(SAMPLE_EMAIL_TEXT)
    assert len(blocks) == 2
    assert "SAAE / DAE / SAMAE" in blocks[0]
    assert "COPASA" in blocks[1]

def test_parse_tender_block(processor):
    """Test parsing of a tender block with the improved implementation."""
    tender = processor._parse_tender_block(SAMPLE_TENDER_BLOCK)
    
    # Test basic instance check
    assert isinstance(tender, TenderNotice)
    
    # Test organization details
    assert tender.organization == "SAAE / DAE / SAMAE - Serviços Autônomos de Água e Esgoto do Municipio"
    assert tender.type == "Municipal"
    assert tender.city == "Aracruz"
    assert tender.state == "ES"
    
    # Test tender details
    assert tender.modality == "CONCORRÊNCIA PÚBLICA ELETRÔNICA"
    assert tender.number == "6/2024"
    
    # Normalize strings for comparison by removing accents and converting to lowercase
    normalized_desc = tender.object_description.lower()
    # Replace newlines with spaces
    normalized_desc = ' '.join(normalized_desc.split())
    print(f"\nOriginal description: {tender.object_description}")
    print(f"Lowercased and joined description: {normalized_desc}")
    for a, b in [('á', 'a'), ('à', 'a'), ('ã', 'a'), ('â', 'a'), ('é', 'e'), ('ê', 'e'), 
                 ('í', 'i'), ('ó', 'o'), ('ô', 'o'), ('õ', 'o'), ('ú', 'u'), ('ç', 'c')]:
        normalized_desc = normalized_desc.replace(a, b)
    print(f"Normalized description: {normalized_desc}")
    print(f"Looking for: 'video monitoramento'")
    assert "video monitoramento" in normalized_desc
    
    assert "Seguranca Eletronica - CFTV, SSTV" in tender.segmentation
    
    # Test date parsing
    assert tender.opening_date == datetime(2024, 11, 21, 9, 0)
    assert tender.id_universo == "10224184"
    
    # Test contact information
    assert len(tender.phones) == 1
    assert "(27) 3256-9409" in tender.phones
    
    # Test access information
    assert len(tender.access_info) == 2
    assert "http://www.saaeara.com.br" in tender.access_info
    assert "licitacao@saaeara.com.br" in tender.access_info
    
    # Test complementary information
    assert "Fonte Diário dos Municipios" in tender.complementary_info

# def test_label_tender(processor, mock_llm):
#     tender = TenderNotice(
#         organization="Test Org",
#         type="Municipal",
#         city="Test City",
#         state="TS",
#         modality="Test Mode",
#         number="123",
#         object_description="Test object",
#         segmentation="Test segment",
#         opening_date=datetime.now(),
#         id_universo="123",
#         phones=[],
#         access_info=[],
#         complementary_info=""
#     )
#     template = "Test template"
#     company_description = "Test company"
#     label = processor._label_tender(tender, template, company_description)
#     assert label == "yes"
#     mock_llm.invoke.assert_called_once()

@patch('os.path.isfile')
@patch('langchain_community.document_loaders.PyPDFLoader')
def test_process_pdf(mock_loader_class, mock_isfile, processor, mock_llm):
    """Test processing of a PDF file containing tender notices."""
    # Create a temporary PDF file with valid PDF structure
    minimal_pdf = b'''%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000052 00000 n
0000000101 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
167
%%EOF'''
    
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_file.write(minimal_pdf)
        tmp_path = tmp_file.name
    
    try:
        # Setup mocks
    mock_isfile.return_value = True

    # Create a mock document with our sample text
    mock_doc = Document(page_content=SAMPLE_EMAIL_TEXT)
        
        # Setup the loader mock to return our document
        mock_loader = MagicMock()
        mock_loader.load.return_value = [mock_doc]
        mock_loader_class.return_value = mock_loader
    
    # Process the PDF
    df = processor.process_pdf(
            tmp_path,
        template="Test template",
        company_description="Test company"
    )
    
    # Test DataFrame structure
    assert len(df) == 2
    expected_columns = {
        'organization', 'type', 'city', 'state', 'modality', 'number',
        'object_description', 'segmentation', 'opening_date', 'id_universo',
        'phones', 'access_info', 'complementary_info', 'label'
    }
    assert all(col in df.columns for col in expected_columns)
    
    # Test first row content
    first_row = df.iloc[0]
    assert first_row['organization'] == "SAAE / DAE / SAMAE - Serviços Autônomos de Água e Esgoto do Municipio"
    assert first_row['type'] == "Municipal"
    assert first_row['city'] == "Aracruz"
    assert first_row['state'] == "ES"
    assert first_row['modality'] == "CONCORRÊNCIA PÚBLICA ELETRÔNICA"
    assert first_row['number'] == "6/2024"
    
    # Normalize strings for comparison
    normalized_desc = first_row['object_description'].lower()
    normalized_desc = ' '.join(normalized_desc.split())
    for a, b in [('á', 'a'), ('à', 'a'), ('ã', 'a'), ('â', 'a'), ('é', 'e'), ('ê', 'e'), 
                 ('í', 'i'), ('ó', 'o'), ('ô', 'o'), ('õ', 'o'), ('ú', 'u'), ('ç', 'c')]:
        normalized_desc = normalized_desc.replace(a, b)
    assert "video monitoramento" in normalized_desc
    
    assert first_row['id_universo'] == "10224184"
    assert isinstance(first_row['phones'], list)
    assert isinstance(first_row['access_info'], list)
    assert first_row['label'] == "yes"  # Based on mock_llm configuration
    
    # Test second row content
    second_row = df.iloc[1]
    assert second_row['organization'] == "COPASA - Cia de Saneamento de Minas Gerais"
    assert second_row['type'] == "Estatal"
    assert second_row['city'] == "Belo Horizonte"
    assert second_row['state'] == "MG"
    assert second_row['modality'] == "LEI DAS ESTATAIS"
    assert second_row['number'] == "820246978"
    assert "Material para estacoes de tratamento" in second_row['object_description']
    assert second_row['id_universo'] == "10224212"
    assert isinstance(second_row['phones'], list)
    assert isinstance(second_row['access_info'], list)
    assert second_row['label'] == "yes"  # Based on mock_llm configuration
    
    # Verify mock calls
        mock_loader_class.assert_called_once_with(file_path=tmp_path)
        mock_loader.load.assert_called_once()
    
    finally:
        # Clean up the temporary file
        os.unlink(tmp_path)

