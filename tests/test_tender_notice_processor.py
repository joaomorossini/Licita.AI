"""Tests for the TenderNoticeProcessor class."""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from src.tender_notice_labeling.tender_notice_processor import TenderNoticeProcessor, TenderNotice

# Sample test data
SAMPLE_TENDER_BLOCK = """
SANEPAR - Cia de Saneamento do Paraná (1/10)
Tipo de Órgão: Estadual Cidade: Curitiba PR
Modalidade: LEI DAS ESTATAIS Nº: 411/2024
Objeto: EXECUCAO DE OBRAS DE AMPLIACAO DO SISTEMA DE ABASTECIMENTO DE AGUA SAA NA ESTACAO DE TRATAMENTO DE AGUA ETA TIBAGI
Segmentação: Engenharia - Saneamento
Abertura: 03/12/2024 10:00
ID Universo: 10223315
Telefone: (41) 3330-3910 Telefone 2: (41) 3330-3901
Acesso: http://licitacao.sanepar.com.br
Complementos: Edital disponível no site
"""

@pytest.fixture
def processor():
    """Create a TenderNoticeProcessor instance with a mock LLM."""
    mock_llm = Mock()
    mock_llm.invoke = Mock(return_value=Mock(content="yes"))
    return TenderNoticeProcessor(llm=mock_llm)

def test_extract_tender_blocks(processor):
    """Test the tender block extraction functionality."""
    blocks = processor._extract_tender_blocks(SAMPLE_TENDER_BLOCK)
    assert len(blocks) == 1
    assert "SANEPAR" in blocks[0]
    assert "Objeto:" in blocks[0]

def test_parse_tender_block(processor):
    """Test parsing of a well-formed tender block."""
    tender = processor._parse_tender_block(SAMPLE_TENDER_BLOCK)
    
    assert isinstance(tender, TenderNotice)
    assert tender.organization == "SANEPAR - Cia de Saneamento do Paraná"
    assert tender.type == "Estadual"
    assert tender.city == "Curitiba"
    assert tender.state == "PR"
    assert tender.modality == "LEI DAS ESTATAIS"
    assert tender.number == "411/2024"
    assert "EXECUCAO DE OBRAS" in tender.object_description
    assert "Engenharia - Saneamento" in tender.segmentation
    assert tender.opening_date == datetime(2024, 12, 3, 10, 0)
    assert tender.id_universo == "10223315"
    assert len(tender.phones) == 2
    assert "(41) 3330-3910" in tender.phones
    assert "http://licitacao.sanepar.com.br" in tender.access_info
    assert "Edital disponível" in tender.complementary_info

def test_parse_tender_block_missing_fields(processor):
    """Test parsing of a tender block with missing fields."""
    incomplete_block = """
    SANEPAR - Cia de Saneamento do Paraná (1/10)
    Tipo de Órgão: Estadual
    Objeto: EXECUCAO DE OBRAS
    """
    tender = processor._parse_tender_block(incomplete_block)
    
    assert isinstance(tender, TenderNotice)
    assert tender.organization == "SANEPAR - Cia de Saneamento do Paraná"
    assert tender.type == "Estadual"
    assert tender.city == ""
    assert tender.state == ""
    assert tender.object_description == "EXECUCAO DE OBRAS"
    assert tender.phones == []
    assert tender.access_info == []
    assert tender.complementary_info == ""

def test_extract_tender_blocks_multiple_patterns(processor):
    """Test extraction of tender blocks using multiple patterns."""
    text = """
    COMPANY A - Services (1/3)
    Tipo de Órgão: Federal
    
    Modalidade: PREGÃO
    Object: Test object
    
    Data Cadastro: 01/01/2024
    Tipo de Órgão: Municipal
    Object: Another test
    """
    blocks = processor._extract_tender_blocks(text)
    assert len(blocks) > 0

