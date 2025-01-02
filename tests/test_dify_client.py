"""Tests for the Dify client module."""

import os
import pytest
import responses
from src.dify_client import (
    DifyClient,
    DifyClientError,
)

# Mock API responses
MOCK_DATASET_RESPONSE = {
    "id": "mock_dataset_id",
    "name": "test_dataset",
}

MOCK_DOCUMENT_RESPONSE = {
    "document": {
        "id": "mock_doc_id",
        "name": "document.pdf",
    }
}

MOCK_CHAT_RESPONSE = 'data: {"answer": "This is a mock answer"}\n\n'


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Set up environment variables for testing."""
    monkeypatch.setenv("DIFY_API_KEY", "test_api_key")
    monkeypatch.setenv("DIFY_KNOWLEDGE_API_KEY", "test_knowledge_api_key")
    monkeypatch.setenv("DIFY_API_URL", "https://test.dify.api")


@pytest.fixture
def dify_client():
    """Create a DifyClient instance for testing."""
    return DifyClient()


@pytest.fixture
def mock_responses():
    """Set up mock responses for API calls."""
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        # Mock dataset creation endpoint
        rsps.add(
            responses.POST,
            "https://test.dify.api/datasets",
            json=MOCK_DATASET_RESPONSE,
            status=200,
        )

        # Mock document upload endpoint
        rsps.add(
            responses.POST,
            "https://test.dify.api/datasets/87c98a6b-bb10-4eec-8992-0ec453751e58/document/create-by-file",
            json=MOCK_DOCUMENT_RESPONSE,
            status=200,
        )

        # Mock chat messages endpoint with streaming response
        rsps.add_callback(
            responses.POST,
            "https://test.dify.api/chat-messages",
            callback=lambda request: (200, {}, MOCK_CHAT_RESPONSE),
        )

        yield rsps


def test_create_dataset(mock_responses, dify_client):
    """Test that create_dataset makes correct API call and returns dataset ID."""
    dataset_id = dify_client.create_dataset("test_dataset", "test description")
    assert dataset_id == "mock_dataset_id"

    # Verify the API was called correctly
    assert len(mock_responses.calls) == 1
    assert mock_responses.calls[0].request.url == "https://test.dify.api/datasets"


def test_upload_pdf_to_dify(mock_responses, dify_client):
    """Test that upload_pdf makes correct API call and returns document ID."""
    doc_id = dify_client.upload_knowledge_file(b"fake_pdf_data", "test.pdf")
    assert doc_id == "mock_doc_id"

    # Verify the API was called correctly
    assert len(mock_responses.calls) == 1
    assert (
        mock_responses.calls[0].request.url
        == "https://test.dify.api/datasets/87c98a6b-bb10-4eec-8992-0ec453751e58/document/create-by-file"
    )


def test_missing_api_key(monkeypatch, dify_client):
    """Test that functions raise error when API key is not set."""
    monkeypatch.delenv("DIFY_API_KEY", raising=False)
    monkeypatch.delenv("DIFY_KNOWLEDGE_API_KEY", raising=False)

    with pytest.raises(
        DifyClientError, match="DIFY_KNOWLEDGE_API_KEY environment variable not set"
    ):
        dify_client.upload_knowledge_file(b"fake_pdf_data", "test.pdf")
