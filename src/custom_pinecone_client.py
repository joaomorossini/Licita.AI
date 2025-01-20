# pip install --upgrade pinecone pinecone-plugin-records
import os
import time
import logging
import asyncio
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from uuid import uuid4
from pinecone import Pinecone, ServerlessSpec

from src.utils import TenderKnowledgeUtils

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CustomPineconeClientError(Exception):
    """Custom exception class for Pinecone client errors."""

    pass


class CustomPineconeClient:
    """Custom Pinecone client wrapper with improved error handling."""

    def __init__(self):
        """Initialize the Pinecone client."""
        try:
            logger.info("Initializing Pinecone client")
            self.client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone client: {str(e)}")
            raise CustomPineconeClientError(
                f"Failed to initialize Pinecone client: {str(e)}"
            )

    def _get_index_host(self, index_name: str) -> str:
        """Get the host for a given index.

        Args:
            index_name: Name of the index

        Returns:
            str: The host URL for the index

        Raises:
            CustomPineconeClientError: If the host cannot be retrieved
        """
        try:
            response = self.client.describe_index(index_name)

            # Get host from response, handling both dict and IndexModel types
            host = None
            if hasattr(response, "host"):  # IndexModel type
                host = response.host
            elif isinstance(response, dict):  # Dictionary type
                host = response.get("host")

            if not host:
                raise CustomPineconeClientError(
                    f"No host found in response: {response}"
                )

            return host

        except CustomPineconeClientError:
            raise
        except Exception as e:
            logger.error(f"Failed to get index host for {index_name}: {str(e)}")
            raise CustomPineconeClientError(
                "Erro ao obter informações da base de conhecimento. Por favor, tente novamente."
            )

    def create_index(self, index_name: str) -> str:
        """Create a new index.

        Args:
            index_name: Name of the index to create

        Returns:
            str: The host URL of the created index

        Raises:
            CustomPineconeClientError: If the index cannot be created
        """
        try:
            # Validate index name
            if not index_name:
                raise CustomPineconeClientError(
                    "O nome da base de conhecimento não pode estar vazio."
                )
            if not all(c.isalnum() or c == "-" for c in index_name):
                raise CustomPineconeClientError(
                    "O nome da base de conhecimento deve conter apenas letras, números e hífens."
                )
            if not index_name.islower():
                raise CustomPineconeClientError(
                    "O nome da base de conhecimento deve estar em letras minúsculas."
                )

            logger.info(f"Creating index: {index_name}")
            self.client.create_index(
                name=index_name,
                dimension=3072,  # Claude 3 Sonnet dimension
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
            return self._get_index_host(index_name)
        except CustomPineconeClientError:
            raise
        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {str(e)}")
            if "400" in str(e):
                raise CustomPineconeClientError(
                    "Erro ao criar a base de conhecimento: o nome contém caracteres inválidos. "
                    "Use apenas letras minúsculas, números e hífens."
                )
            raise CustomPineconeClientError(
                "Erro ao criar a base de conhecimento. Por favor, tente novamente."
            )

    def delete_index(self, index_name: str) -> bool:
        """Delete an index.

        Args:
            index_name: Name of the index to delete

        Returns:
            bool: True if successful

        Raises:
            CustomPineconeClientError: If the index cannot be deleted
        """
        try:
            logger.info(f"Deleting index: {index_name}")
            self.client.delete_index(index_name)
            return True
        except Exception as e:
            logger.error(f"Failed to delete index {index_name}: {str(e)}")
            raise CustomPineconeClientError(f"Failed to delete index: {str(e)}")

    def list_indexes(self) -> List[str]:
        """List all indexes.

        Returns:
            List[str]: List of index names

        Raises:
            CustomPineconeClientError: If indexes cannot be listed
        """
        try:
            logger.info("Listing all indexes")
            indexes = self.client.list_indexes().names()
            logger.info(f"Found {len(indexes)} indexes")
            return indexes
        except Exception as e:
            logger.error(f"Failed to list indexes: {str(e)}")
            raise CustomPineconeClientError(f"Failed to list indexes: {str(e)}")

    def list_namespaces(self, index_name: str) -> List[str]:
        """List all namespaces in an index.

        Args:
            index_name: Name of the index

        Returns:
            List[str]: List of namespace names

        Raises:
            CustomPineconeClientError: If namespaces cannot be listed
        """
        try:
            logger.info(f"Listing namespaces for index: {index_name}")
            index = self.client.Index(index_name)
            stats = index.describe_index_stats()
            namespaces = list(stats.get("namespaces", {}).keys())
            return namespaces
        except Exception as e:
            logger.error(f"Failed to list namespaces for index {index_name}: {str(e)}")
            raise CustomPineconeClientError(f"Failed to list namespaces: {str(e)}")

    def delete_namespace(self, index_name: str, namespace: str) -> bool:
        """Delete a namespace from an index.

        Args:
            index_name: Name of the index
            namespace: Name of the namespace to delete

        Returns:
            bool: True if successful

        Raises:
            CustomPineconeClientError: If the namespace cannot be deleted
        """
        try:
            logger.info(f"Deleting namespace {namespace} from index {index_name}")
            index = self.client.Index(index_name)
            index.delete(deleteAll=True, namespace=namespace)
            return True
        except Exception as e:
            logger.error(
                f"Failed to delete namespace {namespace} from index {index_name}: {str(e)}"
            )
            raise CustomPineconeClientError(f"Failed to delete namespace: {str(e)}")

    def upsert_vectors(
        self,
        index_name: str,
        vectors: List[Dict[str, Any]],
        namespace: Optional[str] = None,
    ) -> None:
        """Upsert vectors to an index.

        Args:
            index_name: Name of the index
            vectors: List of vectors to upsert
            namespace: Optional namespace to upsert to

        Raises:
            CustomPineconeClientError: If vectors cannot be upserted
        """
        try:
            logger.info(
                f"Upserting {len(vectors)} vectors to index {index_name}"
                + (f" namespace {namespace}" if namespace else "")
            )

            # Get index instance
            index = self.client.Index(index_name)

            # Upsert in batches of 100 vectors
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i : i + batch_size]
                logger.info(
                    f"Upserting batch {i//batch_size + 1} of {(len(vectors)-1)//batch_size + 1}"
                )
                index.upsert(vectors=batch, namespace=namespace)

        except Exception as e:
            logger.error(
                f"Failed to upsert vectors to index {index_name}"
                + (f" namespace {namespace}" if namespace else "")
                + f": {str(e)}"
            )
            raise CustomPineconeClientError(f"Failed to upsert vectors: {str(e)}")

    # TODO: Improve search functionality. Reference: https://docs.pinecone.io/guides/data/query-data
    def query_vectors(
        self,
        index_name: str,
        query: str,
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
    ):
        """Query vectors in an index (to be improved).

        Args:
            index_name: Name of the index
            query: Query text
            namespace: Target namespace
            filter: Metadata filters
            top_k: Number of results to return

        Raises:
            CustomPineconeClientError: If query fails
        """
        try:
            logger.info(f"Querying index {index_name} with namespace {namespace}")
            host = self._get_index_host(index_name)
            index = self.client.Index(host=host)

            query_embeddings = self.utils.get_embeddings(text=query)
            results = index.query(
                namespace=namespace,
                vector=query_embeddings,
                filter=filter,
                top_k=top_k,
                include_values=False,
            )
            logger.info(f"Query completed successfully")
            return results
        except Exception as e:
            logger.error(f"Failed to query vectors: {str(e)}")
            raise CustomPineconeClientError(f"Failed to query vectors: {str(e)}", e)
