import logging
import os
import asyncio
from tempfile import TemporaryDirectory
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from uuid import uuid4

import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from openai import AzureOpenAI, APIError

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TenderKnowledgeUtilsError(Exception):
    """Custom exception for TenderKnowledgeUtils errors."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


@dataclass
class ProcessedChunk:
    """Represents a processed text chunk with its metadata."""

    id: str
    text: str
    embedding: Optional[List[float]]
    metadata: Dict[str, Any]
    error: Optional[str] = None


class TenderKnowledgeUtils:
    @staticmethod
    def load_pdfs_to_docs(uploaded_pdfs) -> List[Dict[str, Any]]:
        """Load PDF files into document objects with metadata.

        Args:
            uploaded_pdfs: List of uploaded PDF files

        Returns:
            List[Dict[str, Any]]: List of documents with metadata

        Raises:
            TenderKnowledgeUtilsError: If there's an error processing the PDFs
        """
        logger.info("Loading PDFs to documents")
        all_documents = []
        with TemporaryDirectory() as temp_dir:
            for uploaded_file in uploaded_pdfs:
                try:
                    temp_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(temp_path, "wb") as temp_file:
                        temp_file.write(uploaded_file.getvalue())
                    logger.debug(f"File written to temporary path: {temp_path}")

                    loader = PyPDFLoader(file_path=temp_path)
                    documents = loader.load()
                    logger.info(
                        f"Loaded {len(documents)} pages from {uploaded_file.name}"
                    )

                    # Group documents by source file
                    filename = uploaded_file.name.rsplit(".", 1)[0]
                    processed_docs = []
                    for doc in documents:
                        processed_docs.append(
                            {
                                "content": doc.page_content,
                                "metadata": {
                                    "filename": filename,
                                    "page_number": doc.metadata.get("page", 0) + 1,
                                },
                            }
                        )
                    all_documents.extend(processed_docs)

                except Exception as e:
                    logger.error(
                        f"Error processing document {uploaded_file.name}: {str(e)}"
                    )
                    raise TenderKnowledgeUtilsError(
                        f"Error processing document: {str(e)}", e
                    )

        logger.info(f"Successfully loaded {len(all_documents)} total pages")
        return all_documents

    @staticmethod
    def concatenate_docs(documents):
        """Concatenate multiple documents into a single text, preserving metadata.

        Args:
            documents: List of document objects with page_content and metadata

        Returns:
            str: Concatenated text with page information
        """
        logger.debug("Concatenating documents")
        tender_documents = ""
        for i, doc in enumerate(documents):
            source = doc.metadata.get("source", "")
            filename = source.split("/")[-1]
            filename = filename.split(".")[0]
            tender_documents += f"{filename} - Pág.{i + 1}\n{doc.page_content}\n"
        logger.debug("All documents concatenated")
        return tender_documents

    @staticmethod
    def split_document(
        document: Dict[str, Any], chunk_size: int = 2500, chunk_overlap: int = 250
    ) -> List[ProcessedChunk]:
        """Split a document into chunks while preserving metadata.

        Args:
            document: Document dictionary with content and metadata
            chunk_size: Maximum size of each chunk (default: 2500)
            chunk_overlap: Number of overlapping characters between chunks (default: 250)

        Returns:
            List[ProcessedChunk]: List of processed chunks with metadata

        Raises:
            TenderKnowledgeUtilsError: If there's an error splitting the text
        """
        try:
            logger.debug(
                f"Splitting document page {document['metadata']['page_number']}"
            )

            splitter = RecursiveCharacterTextSplitter(
                separators=["\n\n", "\n", " ", ""],
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=TenderKnowledgeUtils._length_function,
            )

            chunks = splitter.split_text(document["content"])

            processed_chunks = []
            for i, chunk in enumerate(chunks):
                processed_chunks.append(
                    ProcessedChunk(
                        id=str(uuid4()),
                        text=chunk,
                        embedding=None,
                        metadata={
                            **document["metadata"],
                            "chunk_number": i + 1,
                            "total_chunks": len(chunks),
                        },
                    )
                )

            logger.debug(
                f"Split page {document['metadata']['page_number']} into {len(chunks)} chunks"
            )
            return processed_chunks

        except Exception as e:
            logger.error(f"Error splitting document: {str(e)}")
            raise TenderKnowledgeUtilsError(f"Error splitting document: {str(e)}", e)

    @staticmethod
    def _length_function(text: str, encoding: str = "o200k_base") -> int:
        """Calculate the token length of a text string.

        Args:
            text: Input text
            encoding: Tiktoken encoding to use

        Returns:
            int: Number of tokens in the text
        """
        enc = tiktoken.get_encoding(f"{encoding}")
        return len(enc.encode(text))

    @staticmethod
    async def get_embeddings_batch(
        chunks: List[ProcessedChunk],
        batch_size: int = 100,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        max_concurrent_requests: int = 5,
    ) -> List[ProcessedChunk]:
        """Generate embeddings for a batch of text chunks asynchronously.

        Args:
            chunks: List of ProcessedChunk objects
            batch_size: Number of chunks per batch
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries (will be multiplied by attempt number)
            max_concurrent_requests: Maximum number of concurrent API requests

        Returns:
            List[ProcessedChunk]: Chunks with embeddings added

        Raises:
            TenderKnowledgeUtilsError: If there's an error generating embeddings
        """
        try:
            logger.info(f"Generating embeddings for {len(chunks)} chunks")

            client = AzureOpenAI(
                api_version=os.getenv("OPENAI_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            )

            semaphore = asyncio.Semaphore(max_concurrent_requests)

            async def process_chunk(chunk: ProcessedChunk) -> ProcessedChunk:
                async with semaphore:
                    for attempt in range(max_retries):
                        try:
                            result = await asyncio.to_thread(
                                client.embeddings.create,
                                input=chunk.text,
                                model="text-embedding-3-large",
                            )
                            chunk.embedding = result.data[0].embedding
                            return chunk

                        except Exception as e:
                            if attempt == max_retries - 1:
                                logger.error(
                                    f"Failed to generate embedding after {max_retries} attempts: {str(e)}"
                                )
                                chunk.error = str(e)
                                return chunk

                            wait_time = retry_delay * (attempt + 1)
                            logger.warning(
                                f"Attempt {attempt + 1}/{max_retries} failed. Retrying in {wait_time}s"
                            )
                            await asyncio.sleep(wait_time)

            # Process chunks in batches
            processed_chunks = []
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i : i + batch_size]

                # Process batch concurrently
                tasks = [process_chunk(chunk) for chunk in batch]
                batch_results = await asyncio.gather(*tasks)
                processed_chunks.extend(batch_results)

                logger.debug(
                    f"Processed batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}"
                )

            # Check for errors
            error_chunks = [c for c in processed_chunks if c.error is not None]
            if error_chunks:
                logger.warning(
                    f"Failed to generate embeddings for {len(error_chunks)} chunks"
                )

            logger.info(
                f"Successfully generated embeddings for {len(processed_chunks) - len(error_chunks)} chunks"
            )
            return processed_chunks

        except Exception as e:
            logger.error(f"Error in batch embedding generation: {str(e)}")
            raise TenderKnowledgeUtilsError("Error generating embeddings", e)

    @staticmethod
    def prepare_vectors_for_upsert(
        chunks: List[ProcessedChunk],
    ) -> List[Dict[str, Any]]:
        """Prepare processed chunks for upserting to Pinecone.

        Args:
            chunks: List of ProcessedChunk objects

        Returns:
            List[Dict[str, Any]]: List of vectors ready for Pinecone upsert
        """
        return [
            {"id": chunk.id, "values": chunk.embedding, "metadata": chunk.metadata}
            for chunk in chunks
            if chunk.embedding is not None
        ]
