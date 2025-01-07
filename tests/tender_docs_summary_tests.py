import os
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document
from src.tender_docs_summary_chain import TenderDocsSummaryUtils, TenderDocsSummaryChain

# Sample tender document for testing
SAMPLE_TENDER_DOC = """
# Seção 1 - Prazos
- Data limite para entrega: 30/12/2024
- Vigência do contrato: 12 meses

# Seção 2 - Valores
- Valor estimado: R$ 1.000.000,00
- Garantia: 5% do valor total

# Seção 3 - Requisitos Técnicos
- Experiência mínima: 5 anos
- Certificações necessárias: ISO 9001
"""


@pytest.fixture
def test_pdf_file():
    """Load the test PDF file."""
    pdf_path = os.path.join(os.path.dirname(__file__), "test_assets", "test_pdf.pdf")
    with open(pdf_path, "rb") as f:
        content = f.read()

    mock_file = MagicMock()
    mock_file.name = "test_pdf.pdf"
    mock_file.read.return_value = content
    return mock_file


@pytest.fixture
def utils():
    """Create an instance of TenderDocsSummaryUtils."""
    return TenderDocsSummaryUtils()


@pytest.fixture
def chain():
    """Create an instance of TenderDocsSummaryChain."""
    return TenderDocsSummaryChain()


@pytest.fixture
def mock_streamlit():
    """Mock Streamlit components."""
    with patch("streamlit.markdown") as mock_markdown, patch(
        "streamlit.error"
    ) as mock_error, patch("streamlit.spinner") as mock_spinner, patch(
        "streamlit.container"
    ) as mock_container:
        mock_spinner.return_value.__enter__ = lambda x: None
        mock_spinner.return_value.__exit__ = lambda x, y, z, w: None
        mock_container.return_value.__enter__ = lambda x: None
        mock_container.return_value.__exit__ = lambda x, y, z, w: None
        yield {
            "markdown": mock_markdown,
            "error": mock_error,
            "spinner": mock_spinner,
            "container": mock_container,
        }


def test_load_pdfs_to_docs(utils, test_pdf_file):
    """Test loading of the PDF file."""
    docs = utils.load_pdfs_to_docs([test_pdf_file])
    assert len(docs) > 0
    assert all(isinstance(doc, Document) for doc in docs)
    assert all(doc.page_content for doc in docs)


def test_concatenate_docs(utils):
    """Test concatenation of multiple documents."""
    docs = [
        Document(page_content="Content 1", metadata={"source": "file1.pdf"}),
        Document(page_content="Content 2", metadata={"source": "file2.pdf"}),
    ]
    result = utils.concatenate_docs(docs)
    assert "Content 1" in result
    assert "Content 2" in result
    assert "file1.pdf" in result
    assert "file2.pdf" in result


def test_generate_summary_success(chain, mock_streamlit):
    """Test successful generation of summary."""
    with patch.object(
        chain, "_run_section_categorization"
    ) as mock_categorize, patch.object(
        chain, "_run_requirements_step"
    ) as mock_requirements, patch.object(
        chain, "_run_summary_step"
    ) as mock_summary:

        mock_categorize.return_value = "Categorized sections"
        mock_requirements.return_value = "Requirements list"
        mock_summary.return_value.content = "Test summary"

        result = chain.generate_summary(SAMPLE_TENDER_DOC)
        assert result == "Test summary"

        mock_categorize.assert_called_once_with(SAMPLE_TENDER_DOC)
        mock_requirements.assert_called_once_with("Categorized sections")
        mock_summary.assert_called_once_with("Requirements list")


def test_generate_summary_error(chain, mock_streamlit):
    """Test error handling during summary generation."""
    with patch.object(chain, "_run_section_categorization") as mock_categorize:
        mock_categorize.side_effect = Exception("Analysis error")
        chain.generate_summary(SAMPLE_TENDER_DOC)
        mock_streamlit["error"].assert_called_once()


def test_load_pdfs_to_docs_no_documents(utils):
    """Test behavior when no documents are loaded."""
    result = utils.load_pdfs_to_docs([])
    assert result == []


def test_concatenate_docs_without_metadata(utils):
    """Test concatenation of documents without metadata."""
    docs = [
        Document(page_content="Content 1", metadata={"source": "file1.pdf"}),
        Document(page_content="Content 2", metadata={"source": "file2.pdf"}),
    ]
    result = utils.concatenate_docs(docs, include_metadata=False)
    assert "Content 1" in result
    assert "Content 2" in result
    assert "file1.pdf" not in result
    assert "file2.pdf" not in result


def test_load_pdfs_to_docs_corrupted_file(utils):
    """Test handling of corrupted PDF file."""
    mock_file = MagicMock()
    mock_file.name = "corrupted.pdf"
    mock_file.read.side_effect = Exception("Corrupted file")

    # Should not raise exception and return empty list
    result = utils.load_pdfs_to_docs([mock_file])
    assert result == []


def test_run_section_categorization(chain):
    """Test the section categorization step."""
    with patch.object(chain, "llm") as mock_llm:
        mock_llm.invoke.return_value = "Categorized content"
        result = chain._run_section_categorization(SAMPLE_TENDER_DOC)
        assert result == "Categorized content"
        mock_llm.invoke.assert_called_once()


def test_run_requirements_step(chain):
    """Test the requirements analysis step."""
    with patch.object(chain, "llm") as mock_llm:
        mock_llm.invoke.return_value = "Requirements analysis"
        result = chain._run_requirements_step("Categorized sections")
        assert result == "Requirements analysis"
        mock_llm.invoke.assert_called_once()


def test_run_summary_step(chain):
    """Test the summary generation step."""
    with patch.object(chain, "llm") as mock_llm:
        mock_response = MagicMock()
        mock_response.content = "Final summary"
        mock_llm.invoke.return_value = mock_response

        result = chain._run_summary_step("Requirements list")
        assert result.content == "Final summary"
        mock_llm.invoke.assert_called_once()


def test_concatenate_docs_empty_documents(utils):
    """Test concatenation with empty document list."""
    result = utils.concatenate_docs([])
    assert result == ""


def test_concatenate_docs_missing_metadata(utils):
    """Test concatenation when documents are missing metadata."""
    docs = [
        Document(page_content="Content 1", metadata={}),
        Document(page_content="Content 2", metadata={"source": "file2.pdf"}),
    ]
    result = utils.concatenate_docs(docs)
    assert "Content 1" in result
    assert "Content 2" in result
    assert "file2.pdf" in result
