# pip install --upgrade pinecone pinecone-plugin-records
import os
import time
from typing import Any, Dict, List
from dotenv import load_dotenv
from uuid import uuid4
from pinecone.grpc import PineconeGRPC
from pinecone import ServerlessSpec

load_dotenv()


class PineconeClientError(Exception):
    """Custom exception for Dify client errors."""

    def __init__(self, message: str):
        super().__init__(message)


class PineconeClient:
    def __init__(self):
        self.client = PineconeGRPC(api_key=os.getenv("PINECONE_API_KEY"))

    def _get_index_host(self, index_name: str):
        index_info = self.client.describe_index(index_name)
        host = index_info["host"]
        return host

    def create_index(
        self, index_name: str, dimension: int = 3072, metric: str = "cosine"
    ):
        index_model = self.client.create_index(
            name=index_name,
            dimension=dimension,
            metric=metric,
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            deletion_protection="disabled",
        )
        return index_model

    def list_indexes(self):
        indexes = self.client.list_indexes()
        return indexes

    def upsert_vectors(
        self,
        index_name: str,
        embedding_values_list: List[List[float]],
        metadata: Dict[str, Any],
        source_file: str,
        namespace: str = "default",
    ):
        host = self._get_index_host(index_name)
        index = self.client.Index(host=host)

        upsert_response = index.upsert(
            vectors=[
                {
                    "id": str(uuid4()),
                    "values": embedding_values_list[i],
                    "metadata": {"source_file": source_file, **metadata},
                }
                for i in range(len(embedding_values_list))
            ],
            namespace=namespace,
        )
        return upsert_response
