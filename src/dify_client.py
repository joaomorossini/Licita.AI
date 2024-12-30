"""Client for interacting with Dify API."""

import os
import json
import time
import logging
from typing import Optional, Generator
import requests
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = os.getenv("DIFY_API_URL", "https://dify.cogmo.com.br/v1")
DEFAULT_DATASET_ID = "87c98a6b-bb10-4eec-8992-0ec453751e58"


class DifyClientError(Exception):
    """Custom exception for Dify client errors."""

    pass


def get_api_key(for_knowledge: bool = False) -> str:
    """Get the appropriate API key from environment variables.

    Args:
        for_knowledge: Whether to get the Knowledge API key instead of Chat API key

    Returns:
        str: The API key for Dify

    Raises:
        DifyClientError: If required API key environment variable is not set or invalid
    """
    key_name = "DIFY_KNOWLEDGE_API_KEY" if for_knowledge else "DIFY_API_KEY"
    api_key = os.getenv(key_name)

    if not api_key:
        logger.error(f"{key_name} environment variable not set")
        raise DifyClientError(
            f"{key_name} environment variable not set. Please create a .env file with your API key."
        )
    if api_key == "your-api-key-here":
        logger.error(f"{key_name} is still set to the example value")
        raise DifyClientError(
            f"Please replace the example {key_name} in .env with your actual Dify API key"
        )
    logger.info(f"{key_name} loaded successfully")
    return api_key


def log_request_info(method: str, url: str, **kwargs):
    """Log request information for debugging.

    Args:
        method: HTTP method
        url: Request URL
        **kwargs: Request parameters
    """
    logger.info(f"Making {method} request to {url}")
    if "headers" in kwargs:
        # Log headers except Authorization
        safe_headers = {
            k: v for k, v in kwargs["headers"].items() if k.lower() != "authorization"
        }
        logger.info(f"Headers: {safe_headers}")
    if "json" in kwargs:
        logger.info(f"JSON data: {kwargs['json']}")
    if "data" in kwargs:
        logger.info(f"Form data: {kwargs['data']}")
    if "files" in kwargs:
        logger.info("Files included in request")


def create_dataset(name: str, description: str = "Documents for Licita.AI") -> str:
    """Create a new dataset in Dify.

    Args:
        name: Name for the new dataset
        description: Description for the new dataset

    Returns:
        str: The dataset ID from Dify

    Raises:
        DifyClientError: If the dataset creation fails
    """
    try:
        logger.info("Creating new dataset...")
        url = f"{BASE_URL}/datasets"
        headers = {
            "Authorization": f"Bearer {get_api_key(for_knowledge=True)}",
            "Content-Type": "application/json",
        }

        create_data = {
            "name": name,
            "description": description,
            "permission": "only_me",
            "indexing_technique": "high_quality",
        }

        response = requests.post(url, headers=headers, json=create_data)
        if not response.ok:
            logger.error(f"Failed to create dataset: {response.status_code}")
            logger.error(f"Response content: {response.text}")
            response.raise_for_status()

        dataset_id = response.json()["id"]
        logger.info(f"Created dataset {name} with ID: {dataset_id}")
        return dataset_id

    except RequestException as e:
        logger.error(f"Failed to create dataset: {str(e)}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response content: {e.response.text}")
        raise DifyClientError(f"Failed to create dataset: {str(e)}") from e


def upload_pdf(
    file_bytes: bytes, filename: str, dataset_id: Optional[str] = None
) -> str:
    """Upload a PDF file to Dify knowledge base.

    Args:
        file_bytes: The PDF file content as bytes
        filename: The name of the file being uploaded
        dataset_id: Optional dataset ID to use. If not provided, uses the default dataset.

    Returns:
        str: The document ID from Dify

    Raises:
        DifyClientError: If the upload fails
    """
    try:
        # Use provided dataset_id or default
        dataset_id = dataset_id or DEFAULT_DATASET_ID
        logger.info(f"Using dataset ID: {dataset_id}")

        # Create document in the dataset
        url = f"{BASE_URL}/datasets/{dataset_id}/document/create-by-file"

        # Prepare the processing rules
        data = {
            "name": filename,
            "indexing_technique": "high_quality",
            "process_rule": {
                "rules": {
                    "pre_processing_rules": [
                        {"id": "remove_extra_spaces", "enabled": True},
                        {"id": "remove_urls_emails", "enabled": True},
                    ],
                    "segmentation": {"separator": "###", "max_tokens": 500},
                },
                "mode": "custom",
            },
        }

        # Convert data dict to string and create form data
        files = {
            "file": (filename, file_bytes, "application/pdf"),
            "data": (None, json.dumps(data), "text/plain"),
        }

        headers = {"Authorization": f"Bearer {get_api_key(for_knowledge=True)}"}
        log_request_info("POST", url, headers=headers, files=files)

        response = requests.post(url, headers=headers, files=files)

        if not response.ok:
            logger.error(f"Upload failed with status {response.status_code}")
            logger.error(f"Response content: {response.text}")
            response.raise_for_status()

        result = response.json()
        doc_id = result["document"]["id"]
        logger.info(f"PDF uploaded successfully. Document ID: {doc_id}")
        return doc_id

    except RequestException as e:
        logger.error(f"Failed to upload PDF: {str(e)}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response content: {e.response.text}")
        raise DifyClientError(f"Failed to upload PDF: {str(e)}") from e


def chat_with_doc(doc_id: Optional[str], user_query: str) -> Generator[str, None, None]:
    """Chat with the document using Dify.

    Args:
        doc_id: The document ID from Dify (optional)
        user_query: The user's question about the document

    Yields:
        str: Chunks of the response as they arrive

    Raises:
        DifyClientError: If the chat request fails
    """
    try:
        logger.info(
            f"Sending chat query{' for document ' + doc_id if doc_id else ''}..."
        )

        # Send message to the application
        url = f"{BASE_URL}/chat-messages"

        # Base request data following official API documentation
        data = {
            "query": user_query,  # Required: User input/question content
            "inputs": {},  # Optional: Variables defined by the app
            "response_mode": "streaming",  # Use streaming for real-time responses
            "user": "default_user",  # User identifier for analytics
            "auto_generate_name": True,  # Auto-generate conversation title
        }

        # Only include files if we have a document ID
        if doc_id:
            data["files"] = [{"id": doc_id, "type": "pdf"}]

        headers = {
            "Authorization": f"Bearer {get_api_key()}",
            "Content-Type": "application/json",
        }

        log_request_info("POST", url, headers=headers, json=data)

        with requests.post(url, headers=headers, json=data, stream=True) as response:
            if not response.ok:
                logger.error(f"Chat request failed with status {response.status_code}")
                logger.error(f"Response content: {response.text}")
                response.raise_for_status()

            # Process the stream
            for line in response.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        try:
                            # Remove "data: " prefix and parse JSON
                            json_str = line[6:]
                            chunk_data = json.loads(json_str)

                            # Extract the actual text from the response
                            if "answer" in chunk_data:
                                yield chunk_data["answer"]
                            elif "text" in chunk_data:
                                yield chunk_data["text"]
                            elif "event" in chunk_data:
                                if chunk_data["event"] == "error":
                                    error_msg = chunk_data.get(
                                        "message", "Unknown error"
                                    )
                                    logger.error(f"Stream error: {error_msg}")
                                    yield f"❌ Error: {error_msg}"
                                elif chunk_data["event"] == "message":
                                    message = chunk_data.get("message", "")
                                    if message:
                                        yield message

                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse chunk: {str(e)}")
                            continue

    except RequestException as e:
        logger.error(f"Chat request failed: {str(e)}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response content: {e.response.text}")
        raise DifyClientError(f"Chat request failed: {str(e)}") from e
