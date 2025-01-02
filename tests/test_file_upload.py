import requests
import pytest
from unittest.mock import patch, mock_open
from src.dify_client import DifyClient, DifyClientError


@pytest.fixture
def dify_client():
    return DifyClient()


def test_upload_file_success(dify_client):
    file_path = "test_file.txt"
    user_id = "test_user"
    file_content = b"Test file content"

    with patch("builtins.open", mock_open(read_data=file_content)), patch(
        "requests.post"
    ) as mock_post:
        mock_response = mock_post.return_value
        mock_response.ok = True
        mock_response.json.return_value = {
            "id": "file_id",
            "name": "test_file.txt",
            "size": len(file_content),
            "extension": "txt",
            "mime_type": "text/plain",
            "created_by": user_id,
            "created_at": 1705395332,
        }

        response = dify_client.upload_file(file_path, user_id)
        assert response["id"] == "file_id"
        assert response["name"] == "test_file.txt"
        assert response["size"] == len(file_content)
        assert response["extension"] == "txt"
        assert response["mime_type"] == "text/plain"
        assert response["created_by"] == user_id


def test_upload_file_not_found(dify_client):
    file_path = "non_existent_file.txt"
    user_id = "test_user"

    with pytest.raises(DifyClientError, match="File not found"):
        dify_client.upload_file(file_path, user_id)


def test_upload_file_request_exception(dify_client):
    file_path = "test_file.txt"
    user_id = "test_user"
    file_content = b"Test file content"

    with patch("builtins.open", mock_open(read_data=file_content)), patch(
        "requests.post"
    ) as mock_post:
        mock_post.side_effect = requests.RequestException("Request failed")

        with pytest.raises(DifyClientError, match="Failed to upload file"):
            dify_client.upload_file(file_path, user_id)
