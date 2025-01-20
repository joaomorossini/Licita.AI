import logging
import asyncio
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass

from src.custom_pinecone_client import CustomPineconeClient
from src.utils import TenderKnowledgeUtils, ProcessedChunk

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class DocumentProcessingStatus:
    """Status of document processing."""

    filename: str
    total_pages: int
    processed_pages: int
    total_chunks: int
    processed_chunks: int
    status: str  # 'pending', 'processing', 'completed', 'error'
    error: Optional[str] = None


class TenderKnowledge:
    def __init__(self):
        self.client = CustomPineconeClient()
        self.utils = TenderKnowledgeUtils()

    async def process_document(
        self,
        index_name: str,
        document: Dict[str, Any],
        status_callback: Optional[Callable[[DocumentProcessingStatus], None]] = None,
    ) -> DocumentProcessingStatus:
        """Process a single document.

        Args:
            index_name: Name of the index to store vectors
            document: Document to process
            status_callback: Optional callback to report status updates

        Returns:
            DocumentProcessingStatus: Final status of document processing
        """
        try:
            filename = document["metadata"]["filename"]
            logger.info(f"Processing document: {filename}")

            # Initialize status
            status = DocumentProcessingStatus(
                filename=f"{filename}.pdf",
                total_pages=1,
                processed_pages=0,
                total_chunks=0,
                processed_chunks=0,
                status="pending",
            )
            if status_callback:
                status_callback(status)

            # Split document into chunks
            status.status = "processing"
            if status_callback:
                status_callback(status)

            chunks = self.utils.split_document(
                document, chunk_size=1000, chunk_overlap=100
            )
            status.total_chunks = len(chunks)
            logger.info(f"Split document into {len(chunks)} chunks")

            # Generate embeddings
            status.status = "generating_embeddings"
            if status_callback:
                status_callback(status)

            processed_chunks = await self.utils.get_embeddings_batch(chunks)
            error_chunks = [c for c in processed_chunks if c.error is not None]
            if error_chunks:
                raise Exception(
                    f"Failed to generate embeddings for {len(error_chunks)} chunks"
                )

            # Prepare vectors for upsert
            vectors = self.utils.prepare_vectors_for_upsert(processed_chunks)

            # Upsert vectors
            try:
                self.client.upsert_vectors(
                    index_name=index_name,
                    vectors=vectors,
                    namespace=filename,
                )
                status.status = "completed"
                status.processed_chunks = len(chunks)
                status.processed_pages = 1
            except Exception as e:
                logger.error(f"Error upserting vectors: {str(e)}")
                status.status = "error"
                status.error = str(e)

            if status_callback:
                status_callback(status)

            return status

        except Exception as e:
            logger.error(f"Error processing document {filename}: {str(e)}")
            status = DocumentProcessingStatus(
                filename=f"{filename}.pdf",
                total_pages=1,
                processed_pages=0,
                total_chunks=0,
                processed_chunks=0,
                status="error",
                error=str(e),
            )
            if status_callback:
                status_callback(status)
            return status

    async def process_tender_documents(
        self,
        index_name: str,
        uploaded_files: List[Any],
        status_callback: Optional[Callable[[DocumentProcessingStatus], None]] = None,
    ) -> List[DocumentProcessingStatus]:
        """Process multiple tender documents and store them in Pinecone.

        Args:
            index_name: Name of the index to store vectors
            uploaded_files: List of uploaded PDF files
            status_callback: Optional callback to report status updates

        Returns:
            List[DocumentProcessingStatus]: List of processing statuses for each document

        Raises:
            Exception: If there's an error processing the documents
        """
        try:
            logger.info(f"Creating index: {index_name}")
            self.client.create_index(index_name)

            # Load all documents first
            logger.info("Loading documents")
            documents = self.utils.load_pdfs_to_docs(uploaded_files)

            # Process each document
            tasks = []
            for doc in documents:
                task = asyncio.create_task(
                    self.process_document(
                        index_name=index_name,
                        document=doc,
                        status_callback=status_callback,
                    )
                )
                tasks.append(task)

            # Wait for all documents to be processed
            statuses = await asyncio.gather(*tasks, return_exceptions=True)

            # Check for exceptions
            error_statuses = []
            for i, status in enumerate(statuses):
                if isinstance(status, Exception):
                    logger.error(f"Error processing document: {str(status)}")
                    error_statuses.append(
                        DocumentProcessingStatus(
                            filename=uploaded_files[i].name,
                            total_pages=1,
                            processed_pages=0,
                            total_chunks=0,
                            processed_chunks=0,
                            status="error",
                            error=str(status),
                        )
                    )
                else:
                    error_statuses.append(status)

            return error_statuses

        except Exception as e:
            logger.error(f"Error processing tender documents: {str(e)}")
            raise
