import os
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import warnings
from typing import List

# Suppress Streamlit warnings in tests
warnings.filterwarnings("ignore", category=Warning)

from src.utils import TenderKnowledgeUtils, ProcessedChunk
from src.custom_pinecone_client import CustomPineconeClient, CustomPineconeClientError
from src.tender_knowledge import TenderKnowledge, DocumentProcessingStatus


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
def mock_pinecone_client():
    """Fixture to provide a mocked Pinecone client."""
    with patch("src.custom_pinecone_client.PineconeGRPC") as mock_grpc:
        client = CustomPineconeClient()
        # Mock successful index creation
        mock_grpc.return_value.create_index.return_value = None
        mock_grpc.return_value.describe_index.return_value = {"host": "test-host"}
        # Mock successful index operations
        mock_index = Mock()
        mock_index.upsert = AsyncMock()
        mock_grpc.return_value.Index.return_value = mock_index
        yield client


@pytest.fixture
def mock_utils():
    """Fixture to provide mocked TenderKnowledgeUtils."""
    utils = TenderKnowledgeUtils()

    # Create sample documents
    sample_docs = [
        {
            "content": "Test content page 1",
            "metadata": {"filename": "test_pdf", "page_number": 1},
        },
        {
            "content": "Test content page 2",
            "metadata": {"filename": "test_pdf", "page_number": 2},
        },
    ]

    # Create sample chunks (2 chunks per page)
    sample_chunks = []
    for page in range(1, 3):  # 2 pages
        for chunk in range(1, 3):  # 2 chunks per page
            sample_chunks.append(
                ProcessedChunk(
                    id=f"chunk{page}_{chunk}",
                    text=f"Test content page {page} chunk {chunk}",
                    embedding=None,
                    metadata={
                        "filename": "test_pdf",
                        "page_number": page,
                        "chunk_number": chunk,
                    },
                )
            )

    # Mock the methods
    with patch.object(
        utils, "load_pdfs_to_docs", return_value=sample_docs
    ), patch.object(
        utils,
        "split_document",
        side_effect=lambda doc: [
            chunk
            for chunk in sample_chunks
            if chunk.metadata["page_number"] == doc["metadata"]["page_number"]
        ],
    ), patch.object(
        utils, "_length_function", return_value=100
    ), patch.object(
        utils, "get_embeddings_batch", new_callable=AsyncMock
    ) as mock_get_embeddings:
        # Configure the mock to return processed chunks with embeddings
        mock_get_embeddings.return_value = [
            ProcessedChunk(
                id=chunk.id,
                text=chunk.text,
                embedding=[0.1] * 3072,
                metadata=chunk.metadata,
            )
            for chunk in sample_chunks
        ]
        yield utils


@pytest.fixture
def tender_knowledge(mock_pinecone_client, mock_utils):
    """Fixture to provide a TenderKnowledge instance with mocked dependencies."""
    with patch("src.tender_knowledge.CustomPineconeClient") as mock_client_class, patch(
        "src.tender_knowledge.TenderKnowledgeUtils"
    ) as mock_utils_class:
        mock_client_class.return_value = mock_pinecone_client
        mock_utils_class.return_value = mock_utils
        return TenderKnowledge()


@pytest.mark.asyncio
async def test_successful_document_processing(tender_knowledge, sample_pdf):
    """Test successful processing of a single document."""
    # Mock status callback
    status_updates = []

    def status_callback(status: DocumentProcessingStatus):
        # Create a new status object to avoid reference issues
        status_updates.append(
            DocumentProcessingStatus(
                filename=status.filename,
                total_pages=status.total_pages,
                processed_pages=status.processed_pages,
                total_chunks=status.total_chunks,
                processed_chunks=status.processed_chunks,
                status=status.status,
                error=status.error,
            )
        )

    status = await tender_knowledge.process_document(
        file=sample_pdf,
        index_name="test-tender",
        status_callback=status_callback,
    )

    # Verify final status
    assert status.status == "completed"
    assert status.filename == "test_pdf.pdf"
    assert status.total_pages == 2
    assert status.processed_pages == 2
    assert status.total_chunks == 4  # 2 chunks per page
    assert status.processed_chunks == 4
    assert status.error is None

    # Verify status updates
    assert len(status_updates) > 0
    status_sequence = [s.status for s in status_updates]
    assert "pending" in status_sequence
    assert "processing" in status_sequence
    assert "generating_embeddings" in status_sequence
    assert "completed" in status_sequence
    assert status_sequence.index("pending") < status_sequence.index("processing")
    assert status_sequence.index("processing") < status_sequence.index(
        "generating_embeddings"
    )
    assert status_sequence.index("generating_embeddings") < status_sequence.index(
        "completed"
    )


@pytest.mark.asyncio
async def test_document_processing_with_embedding_error(tender_knowledge, sample_pdf):
    """Test document processing when embedding generation fails."""
    # Mock embedding generation to fail
    with patch.object(
        tender_knowledge.utils, "get_embeddings_batch", new_callable=AsyncMock
    ) as mock_get_embeddings:
        mock_get_embeddings.side_effect = Exception("API Error")

        with pytest.raises(Exception) as exc_info:
            await tender_knowledge.process_document(
                file=sample_pdf,
                index_name="test-tender",
            )

        assert "API Error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_successful_tender_documents_processing(tender_knowledge, sample_pdf):
    """Test successful processing of multiple tender documents."""
    statuses = await tender_knowledge.process_tender_documents(
        index_name="test-tender",
        uploaded_files=[sample_pdf, sample_pdf],  # Process two copies of the same PDF
    )

    # Verify all documents were processed successfully
    assert len(statuses) == 2
    for status in statuses:
        assert status.status == "completed"
        assert status.error is None


@pytest.mark.asyncio
async def test_tender_documents_processing_with_mixed_results(
    tender_knowledge, sample_pdf
):
    """Test processing multiple documents with mixed success/failure results."""
    # Mock embedding generation to succeed for first document and fail for second
    original_get_embeddings = tender_knowledge.utils.get_embeddings_batch
    call_count = 0

    async def mock_get_embeddings(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return await original_get_embeddings(*args, **kwargs)
        raise Exception("API Error")

    with patch.object(
        tender_knowledge.utils,
        "get_embeddings_batch",
        side_effect=mock_get_embeddings,
    ):
        statuses = await tender_knowledge.process_tender_documents(
            index_name="test-tender",
            uploaded_files=[sample_pdf, sample_pdf],
        )

        # Verify mixed results
        assert len(statuses) == 2
        assert any(s.status == "completed" for s in statuses)
        assert any(s.status == "error" for s in statuses)
