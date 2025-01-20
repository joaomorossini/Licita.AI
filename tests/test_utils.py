import os
import pytest
from unittest.mock import Mock, patch
import asyncio
from typing import List
import warnings

# Suppress Streamlit warnings in tests
warnings.filterwarnings("ignore", category=Warning)

from openai import APIError
from src.utils import (
    TenderKnowledgeUtils,
    TenderKnowledgeUtilsError,
    ProcessedChunk,
)


class MockPDFFile:
    """Mock class to simulate uploaded PDF files in Streamlit."""

    def __init__(self, name: str, content: bytes):
        self.name = name
        self._content = content

    def getvalue(self):
        return self._content


@pytest.fixture
def sample_pdf():
    """Fixture to provide a sample PDF file for testing."""
    pdf_path = os.path.join(os.path.dirname(__file__), "test_assets", "test_pdf.pdf")
    with open(pdf_path, "rb") as f:
        content = f.read()
    return MockPDFFile("test_pdf.pdf", content)


@pytest.fixture
def sample_document():
    """Fixture to provide a sample document for testing."""
    return {
        "content": "This is a test document.\nIt has multiple lines.\nAnd some content.",
        "metadata": {"filename": "test_doc", "page_number": 1},
    }


@pytest.fixture
def sample_chunks() -> List[ProcessedChunk]:
    """Fixture to provide sample processed chunks for testing."""
    return [
        ProcessedChunk(
            id="1",
            text="Chunk 1",
            embedding=None,
            metadata={"filename": "test", "page_number": 1, "chunk_number": 1},
        ),
        ProcessedChunk(
            id="2",
            text="Chunk 2",
            embedding=None,
            metadata={"filename": "test", "page_number": 1, "chunk_number": 2},
        ),
    ]


def test_load_pdfs_to_docs(sample_pdf):
    """Test loading PDF files into documents."""
    utils = TenderKnowledgeUtils()
    docs = utils.load_pdfs_to_docs([sample_pdf])

    assert isinstance(docs, list)
    assert len(docs) > 0
    for doc in docs:
        assert "content" in doc
        assert "metadata" in doc
        assert "filename" in doc["metadata"]
        assert "page_number" in doc["metadata"]
        assert doc["metadata"]["filename"] == "test_pdf"


def test_load_pdfs_to_docs_error():
    """Test error handling when loading invalid PDF files."""
    utils = TenderKnowledgeUtils()
    invalid_pdf = MockPDFFile("invalid.pdf", b"not a pdf")

    with pytest.raises(TenderKnowledgeUtilsError) as exc_info:
        utils.load_pdfs_to_docs([invalid_pdf])

    assert "Error processing document" in str(exc_info.value)


def test_split_document(sample_document):
    """Test splitting a document into chunks."""
    utils = TenderKnowledgeUtils()
    chunks = utils.split_document(sample_document)

    assert isinstance(chunks, list)
    assert len(chunks) > 0
    for chunk in chunks:
        assert isinstance(chunk, ProcessedChunk)
        assert chunk.id is not None
        assert chunk.text is not None
        assert chunk.embedding is None
        assert chunk.metadata["filename"] == sample_document["metadata"]["filename"]
        assert (
            chunk.metadata["page_number"] == sample_document["metadata"]["page_number"]
        )
        assert "chunk_number" in chunk.metadata
        assert "total_chunks" in chunk.metadata


@pytest.mark.asyncio
async def test_get_embeddings_batch(sample_chunks):
    """Test generating embeddings for chunks in batches."""
    utils = TenderKnowledgeUtils()

    # Mock the OpenAI client response
    mock_embedding = [0.1] * 3072  # text-embedding-3-large dimension
    mock_response = Mock()
    mock_response.data = [Mock(embedding=mock_embedding)]

    with patch("openai.AzureOpenAI") as mock_client:
        mock_instance = Mock()
        mock_instance.embeddings.create.return_value = mock_response
        mock_client.return_value = mock_instance

        processed_chunks = await utils.get_embeddings_batch(
            sample_chunks, batch_size=1, max_retries=1
        )

        assert len(processed_chunks) == len(sample_chunks)
        for chunk in processed_chunks:
            assert chunk.embedding is not None
            assert len(chunk.embedding) == 3072
            assert chunk.error is None


@pytest.mark.asyncio
async def test_get_embeddings_batch_error(sample_chunks):
    """Test error handling in batch embedding generation."""
    utils = TenderKnowledgeUtils()

    with patch("src.utils.AzureOpenAI") as mock_client:
        mock_instance = Mock()
        mock_instance.embeddings.create.side_effect = Exception("API Error")
        mock_client.return_value = mock_instance

        processed_chunks = await utils.get_embeddings_batch(
            sample_chunks, batch_size=1, max_retries=1
        )

        assert len(processed_chunks) == len(sample_chunks)
        for chunk in processed_chunks:
            assert chunk.embedding is None
            assert chunk.error is not None
            assert "API Error" in chunk.error


def test_prepare_vectors_for_upsert(sample_chunks):
    """Test preparing processed chunks for Pinecone upsert."""
    utils = TenderKnowledgeUtils()

    # Add mock embeddings to chunks
    mock_embedding = [0.1] * 3072
    for chunk in sample_chunks:
        chunk.embedding = mock_embedding

    vectors = utils.prepare_vectors_for_upsert(sample_chunks)

    assert len(vectors) == len(sample_chunks)
    for vector in vectors:
        assert "id" in vector
        assert "values" in vector
        assert "metadata" in vector
        assert len(vector["values"]) == 3072


def test_concatenate_docs():
    """Test concatenating documents with metadata."""

    class MockDoc:
        def __init__(self, content: str, source: str):
            self.page_content = content
            self.metadata = {"source": source}

    docs = [
        MockDoc("Content 1", "/path/to/doc1.pdf"),
        MockDoc("Content 2", "/path/to/doc2.pdf"),
    ]

    utils = TenderKnowledgeUtils()
    result = utils.concatenate_docs(docs)

    assert isinstance(result, str)
    assert "doc1 - Pág.1" in result
    assert "Content 1" in result
    assert "doc2 - Pág.2" in result
    assert "Content 2" in result
