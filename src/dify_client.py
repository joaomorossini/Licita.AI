"""Client for interacting with Dify API."""

import os
import json
import time
import logging
from typing import Optional, Generator
import requests
from requests.exceptions import RequestException

#############################################
# CRITICAL: Logging Configuration
# DO NOT disable logging as it's essential for debugging
#############################################

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#############################################
# CRITICAL: API Configuration
# These values affect all API operations
#############################################

# Constants
BASE_URL = os.getenv("DIFY_API_URL", "https://dify.cogmo.com.br/v1")
DEFAULT_DATASET_ID = "87c98a6b-bb10-4eec-8992-0ec453751e58"

# Validate base URL
if not BASE_URL:
    raise EnvironmentError("DIFY_API_URL environment variable not set")
if not BASE_URL.startswith(("http://", "https://")):
    raise EnvironmentError("DIFY_API_URL must start with http:// or https://")


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


def validate_api_response(response: requests.Response, operation: str):
    """Validate API response and provide detailed error information.

    Args:
        response: Response object from requests
        operation: Description of the operation being performed

    Raises:
        DifyClientError: If the response indicates an error
    """
    if not response.ok:
        error_msg = f"{operation} failed with status {response.status_code}"
        try:
            error_details = response.json()
            if isinstance(error_details, dict):
                error_msg += f": {error_details.get('message', 'Unknown error')}"
        except json.JSONDecodeError:
            error_msg += f": {response.text}"

        logger.error(error_msg)
        logger.error(f"Response headers: {dict(response.headers)}")
        raise DifyClientError(error_msg)


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


def get_mime_type(filename: str) -> str:
    """Get the MIME type for a file based on its extension.

    Args:
        filename: Name of the file

    Returns:
        str: MIME type for the file
    """
    extension = filename.lower().split(".")[-1]
    mime_types = {
        "txt": "text/plain",
        "md": "text/markdown",
        "markdown": "text/markdown",
        "pdf": "application/pdf",
        "html": "text/html",
        "htm": "text/html",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xls": "application/vnd.ms-excel",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "csv": "text/csv",
    }
    return mime_types.get(extension, "application/octet-stream")


def upload_knowledge_file(
    file_bytes: bytes, filename: str, dataset_id: Optional[str] = None
) -> str:
    """Upload a file to Dify knowledge base.

    Args:
        file_bytes: The file content as bytes
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

        # Get the appropriate MIME type
        mime_type = get_mime_type(filename)
        logger.info(f"Using MIME type: {mime_type} for file: {filename}")

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
            "file": (filename, file_bytes, mime_type),
            "data": (None, json.dumps(data), "text/plain"),
        }

        headers = {"Authorization": f"Bearer {get_api_key(for_knowledge=True)}"}
        log_request_info("POST", url, headers=headers, files=files)

        # Add debug logging for request details
        logger.info(f"Request URL: {url}")
        logger.info(f"Request data structure: {json.dumps(data, indent=2)}")
        logger.info(f"File size: {len(file_bytes)} bytes")

        response = requests.post(url, headers=headers, files=files)

        if not response.ok:
            logger.error(f"Upload failed with status {response.status_code}")
            logger.error(f"Response content: {response.text}")
            logger.error(f"Response headers: {dict(response.headers)}")
            response.raise_for_status()

        result = response.json()
        doc_id = result["document"]["id"]
        logger.info(f"Document uploaded successfully. Document ID: {doc_id}")
        return doc_id

    except RequestException as e:
        logger.error(f"Failed to upload document: {str(e)}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response content: {e.response.text}")
            logger.error(
                f"Response headers: {dict(e.response.headers) if e.response.headers else 'No headers'}"
            )
        raise DifyClientError(f"Failed to upload document: {str(e)}") from e


def stream_dify_response(doc_id: str, prompt: str):
    """
    Get streaming response from Dify API.

    Args:
        doc_id (str): The conversation/document ID
        prompt (str): The user's input message

    Yields:
        tuple: A tuple containing (message_content, conversation_id, is_end)
            - message_content (str): The content chunk from the response
            - conversation_id (str): Updated conversation ID (only on message_end event)
            - is_end (bool): Whether this is the final message chunk
    """
    headers = {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }

    payload = {
        "inputs": {},
        "query": prompt,
        "response_mode": "streaming",
        "conversation_id": doc_id,
        "user": "user",
        "files": [],
    }

    with requests.post(
        f"{BASE_URL}/chat-messages", headers=headers, json=payload, stream=True
    ) as response:
        response.raise_for_status()

        for line in response.iter_lines():
            if not line:
                continue

            line = line.decode("utf-8")
            if not line.startswith("data: "):
                continue

            try:
                event_data = json.loads(line[6:])  # Skip 'data: ' prefix

                if event_data.get("event") == "agent_message":
                    message_content = event_data.get("answer", "")
                    if message_content:
                        yield message_content, None, False

                elif event_data.get("event") == "message_end":
                    conversation_id = event_data.get("conversation_id", doc_id)
                    yield "", conversation_id, True

            except json.JSONDecodeError:
                continue
