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


class DifyClientError(Exception):
    """Custom exception for Dify client errors."""

    def __init__(self, message: str):
        super().__init__(message)


class DifyClient:
    """Client for interacting with Dify API."""

    def __init__(
        self, base_url: Optional[str] = None, default_dataset_id: Optional[str] = None
    ):
        """Initialize the Dify client.

        Args:
            base_url: Optional base URL for the Dify API. Defaults to environment variable.
            default_dataset_id: Optional default dataset ID. Defaults to predefined constant.
        """
        self.base_url = base_url or os.getenv(
            "DIFY_API_URL", "https://dify.cogmo.com.br/v1"
        )
        self.default_dataset_id = (
            default_dataset_id or "87c98a6b-bb10-4eec-8992-0ec453751e58"
        )

        # Validate base URL
        if not self.base_url:
            raise EnvironmentError("DIFY_API_URL environment variable not set")
        if not self.base_url.startswith(("http://", "https://")):
            raise EnvironmentError("DIFY_API_URL must start with http:// or https://")

    def _get_api_key(self, for_knowledge: bool = False) -> str:
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

    def _validate_api_response(self, response: requests.Response, operation: str):
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

    def _log_request_info(self, method: str, url: str, **kwargs):
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
                k: v
                for k, v in kwargs["headers"].items()
                if k.lower() != "authorization"
            }
            logger.info(f"Headers: {safe_headers}")
        if "json" in kwargs:
            logger.info(f"JSON data: {kwargs['json']}")
        if "data" in kwargs:
            logger.info(f"Form data: {kwargs['data']}")
        if "files" in kwargs:
            logger.info("Files included in request")

    def create_dataset(self, name: str) -> str:
        """Create a new dataset in Dify.

        Args:
            name: The name of the dataset

        Returns:
            str: The ID of the created dataset

        Raises:
            DifyClientError: If the creation fails
        """
        try:
            url = f"{self.base_url}/datasets"
            headers = {
                "Authorization": f"Bearer {self._get_api_key(for_knowledge=True)}",
                "Content-Type": "application/json",
            }
            data = {
                "name": name,
                "description": f"Útil para buscar informações relevantes referentes à licitação: {name}",
                "permission": "only_me",
                "indexing_technique": "high_quality",
            }
            self._log_request_info("POST", url, headers=headers, data=data)

            response = requests.post(url, headers=headers, json=data)
            self._validate_api_response(response, "Create dataset")

            dataset = response.json()
            return dataset["id"]

        except RequestException as e:
            logger.error(f"Failed to create dataset: {str(e)}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response content: {e.response.text}")
            raise DifyClientError(f"Failed to create dataset: {str(e)}") from e

    def _get_mime_type(self, filename: str) -> str:
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
        self, file_bytes: bytes, filename: str, dataset_id: Optional[str] = None
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
            dataset_id = dataset_id or self.default_dataset_id
            logger.info(f"Using dataset ID: {dataset_id}")

            # Create document in the dataset
            url = f"{self.base_url}/datasets/{dataset_id}/document/create-by-file"

            # Get the appropriate MIME type
            mime_type = self._get_mime_type(filename)
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

            headers = {
                "Authorization": f"Bearer {self._get_api_key(for_knowledge=True)}"
            }
            self._log_request_info("POST", url, headers=headers, files=files)

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

    def upload_file(self, file_path: str, user_id: str) -> dict:
        """Upload a file to Dify for multimodal understanding.

        Args:
            file_path: The path to the file being uploaded
            user_id: Unique identifier for the user

        Returns:
            dict: Information about the uploaded file

        Raises:
            DifyClientError: If the upload fails
        """
        try:
            with open(file_path, "rb") as file:
                file_bytes = file.read()

            filename = os.path.basename(file_path)
            url = f"{self.base_url}/files/upload"
            mime_type = self._get_mime_type(filename)
            files = {
                "file": (filename, file_bytes, mime_type),
                "user": (None, user_id),
            }
            headers = {
                "Authorization": f"Bearer {self._get_api_key()}",
            }
            self._log_request_info("POST", url, headers=headers, files=files)

            response = requests.post(url, headers=headers, files=files)
            self._validate_api_response(response, "File upload")

            return response.json()

        except RequestException as e:
            logger.error(f"Failed to upload file: {str(e)}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response content: {e.response.text}")
            raise DifyClientError(f"Failed to upload file: {str(e)}") from e
        except FileNotFoundError:
            raise DifyClientError(f"File not found: {file_path}")
        except Exception as e:
            raise DifyClientError(f"An unexpected error occurred: {str(e)}")

    def stream_dify_response(self, conversation_id: str, prompt: str):
        """Get streaming response from Dify API.

        Args:
            conversation_id (str): The conversation/document ID
            prompt (str): The user's input message

        Yields:
            tuple: A tuple containing (message_content, conversation_id, is_end)
                - message_content (str): The content chunk from the response
                - conversation_id (str): Updated conversation ID (only on message_end event)
                - is_end (bool): Whether this is the final message chunk
        """
        headers = {
            "Authorization": f"Bearer {self._get_api_key()}",
            "Content-Type": "application/json",
        }

        payload = {
            "inputs": {},
            "query": prompt,
            "response_mode": "streaming",
            "conversation_id": conversation_id,
            "user": "user",
            "files": [],
        }

        with requests.post(
            f"{self.base_url}/chat-messages", headers=headers, json=payload, stream=True
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

                    if event_data.get("event") == "message":
                        message_content = event_data.get("answer", "")
                        if message_content:
                            yield message_content, None, False

                    elif event_data.get("event") == "message_end":
                        conversation_id = event_data.get(
                            "conversation_id", conversation_id
                        )
                        yield "", conversation_id, True

                except json.JSONDecodeError:
                    continue

    def fetch_all_datasets(self, page: int = 1, limit: int = 20) -> list:
        """Fetch all datasets whose names start with '_-_' and return only id, name, and description.

        Args:
            page: Page number for pagination.
            limit: Number of items per page.

        Returns:
            list: A list of dictionaries containing id, name, and description of each dataset.

        Raises:
            DifyClientError: If the request fails.
        """
        try:
            url = f"{self.base_url}/datasets"
            headers = {
                "Authorization": f"Bearer {self._get_api_key(for_knowledge=True)}",
                "Content-Type": "application/json",
            }
            params = {"page": page, "limit": limit}
            self._log_request_info("GET", url, headers=headers, params=params)

            response = requests.get(url, headers=headers, params=params)
            self._validate_api_response(response, "Fetch all datasets")

            datasets = response.json().get("data", [])
            filtered_datasets = [
                {
                    "id": dataset["id"],
                    "name": dataset["name"],
                    "description": dataset["description"],
                }
                for dataset in datasets
                if dataset["name"].startswith("_-_")
            ]
            return filtered_datasets

        except RequestException as e:
            logger.error(f"Failed to fetch datasets: {str(e)}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response content: {e.response.text}")
            raise DifyClientError(f"Failed to fetch datasets: {str(e)}") from e

    def list_dataset_files(
        self, dataset_id: str, page: int = 1, limit: int = 20
    ) -> list:
        """List all files (documents) in a specific dataset.

        Args:
            dataset_id: The ID of the dataset.
            page: Page number for pagination.
            limit: Number of items per page.

        Returns:
            list: A list of dictionaries containing information about each document.

        Raises:
            DifyClientError: If the request fails.
        """
        try:
            url = f"{self.base_url}/datasets/{dataset_id}/documents"
            headers = {
                "Authorization": f"Bearer {self._get_api_key(for_knowledge=True)}",
                "Content-Type": "application/json",
            }
            params = {"page": page, "limit": limit}
            self._log_request_info("GET", url, headers=headers, params=params)

            response = requests.get(url, headers=headers, params=params)
            self._validate_api_response(response, "List dataset files")

            documents = response.json().get("data", [])
            return documents

        except RequestException as e:
            logger.error(f"Failed to list dataset files: {str(e)}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response content: {e.response.text}")
            raise DifyClientError(f"Failed to list dataset files: {str(e)}") from e

    def delete_dataset(self, dataset_id: str) -> bool:
        """Delete a dataset from Dify.

        Args:
            dataset_id: The ID of the dataset to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            DifyClientError: If the deletion fails
        """
        try:
            url = f"{self.base_url}/datasets/{dataset_id}"
            headers = {
                "Authorization": f"Bearer {self._get_api_key(for_knowledge=True)}"
            }
            self._log_request_info("DELETE", url, headers=headers)

            response = requests.delete(url, headers=headers)
            self._validate_api_response(response, "Delete dataset")
            return True

        except RequestException as e:
            logger.error(f"Failed to delete dataset: {str(e)}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response content: {e.response.text}")
            raise DifyClientError(f"Failed to delete dataset: {str(e)}") from e

    def get_dataset_status(self, dataset_id: str) -> tuple[str, str, str]:
        """Get the overall status of a dataset based on its documents' status.

        Args:
            dataset_id: The ID of the dataset to check

        Returns:
            tuple: Contains (status_type, status_icon, status_text)
                - status_type: 'success', 'warning', or 'error'
                - status_icon: Emoji indicator
                - status_text: Human readable status message
        """
        try:
            documents = self.list_dataset_files(dataset_id)
            if not documents:
                return "success", "✅", "Sem documentos"

            has_processing = False
            has_error = False

            for doc in documents:
                status = doc.get("indexing_status", "").lower()
                if status in ["waiting", "indexing", "parsing", "cleaning"]:
                    has_processing = True
                elif status == "error" or doc.get("error"):
                    has_error = True

            if has_error:
                return "error", "❌", "Erro no processamento"
            elif has_processing:
                return "warning", "⏳", "Processando..."
            else:
                return "success", "✅", "Processado"

        except Exception as e:
            return "error", "❌", f"Erro: {str(e)}"

    def get_document_status_indicator(self, status: str) -> str:
        """Get the visual indicator for a document's status.

        Args:
            status: The status string from the document

        Returns:
            str: An emoji indicating the status (✅ for success, ⏳ for processing, ❌ for error)
        """
        status = status.lower()
        if status == "completed":
            return "✅"
        elif status in ["waiting", "indexing", "parsing", "cleaning"]:
            return "⏳"
        else:
            return "❌"
