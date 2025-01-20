import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any

from src.custom_pinecone_client import CustomPineconeClient, CustomPineconeClientError


@pytest.fixture
def mock_pinecone():
    """Fixture to provide a mocked Pinecone client."""
    with patch("src.custom_pinecone_client.Pinecone") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def client(mock_pinecone):
    """Fixture to provide a CustomPineconeClient instance with mocked Pinecone."""
    return CustomPineconeClient()


def test_initialization(mock_pinecone):
    """Test successful client initialization."""
    client = CustomPineconeClient()
    assert client.client == mock_pinecone


def test_initialization_error():
    """Test client initialization with error."""
    with patch("src.custom_pinecone_client.Pinecone") as mock:
        mock.side_effect = Exception("Connection error")
        with pytest.raises(CustomPineconeClientError) as exc_info:
            CustomPineconeClient()
        assert "Failed to initialize Pinecone client" in str(exc_info.value)


def test_get_index_host(client, mock_pinecone):
    """Test successful index host retrieval."""
    # Test with IndexModel type response
    mock_index_model = MagicMock()
    mock_index_model.host = "test-host.pinecone.io"
    mock_pinecone.describe_index.return_value = mock_index_model

    host = client._get_index_host("test-index")
    assert host == "test-host.pinecone.io"
    mock_pinecone.describe_index.assert_called_once_with("test-index")

    # Reset mock
    mock_pinecone.describe_index.reset_mock()

    # Test with dictionary type response
    mock_response = {
        "deletion_protection": "disabled",
        "dimension": 3072,
        "host": "test-host-2.pinecone.io",
        "metric": "cosine",
        "name": "test-index",
        "spec": {"serverless": {"cloud": "aws", "region": "us-east-1"}},
        "status": {"ready": True, "state": "Ready"},
    }
    mock_pinecone.describe_index.return_value = mock_response

    host = client._get_index_host("test-index")
    assert host == "test-host-2.pinecone.io"
    mock_pinecone.describe_index.assert_called_once_with("test-index")


def test_get_index_host_error(client, mock_pinecone):
    """Test index host retrieval with error."""
    # Test missing host in IndexModel
    mock_index_model = MagicMock()
    delattr(mock_index_model, "host")  # Ensure no host attribute
    mock_pinecone.describe_index.return_value = mock_index_model
    with pytest.raises(CustomPineconeClientError) as exc_info:
        client._get_index_host("test-index")
    assert "No host found" in str(exc_info.value)

    # Test missing host in dict
    mock_pinecone.describe_index.return_value = {"name": "test-index"}
    with pytest.raises(CustomPineconeClientError) as exc_info:
        client._get_index_host("test-index")
    assert "No host found" in str(exc_info.value)

    # Test API error
    mock_pinecone.describe_index.side_effect = Exception("API Error")
    with pytest.raises(CustomPineconeClientError) as exc_info:
        client._get_index_host("test-index")
    assert "Erro ao obter informações" in str(exc_info.value)


def test_create_index(client, mock_pinecone):
    """Test successful index creation."""
    # Mock successful index creation
    mock_pinecone.create_index.return_value = None
    mock_pinecone.describe_index.return_value = {"host": "test-host.pinecone.io"}

    host = client.create_index("test-index")
    assert host == "test-host.pinecone.io"
    mock_pinecone.create_index.assert_called_once()


def test_create_index_validation(client):
    """Test index name validation."""
    # Test empty name
    with pytest.raises(CustomPineconeClientError) as exc_info:
        client.create_index("")
    assert "não pode estar vazio" in str(exc_info.value)

    # Test invalid characters
    with pytest.raises(CustomPineconeClientError) as exc_info:
        client.create_index("Test Index!")
    assert "apenas letras, números e hífens" in str(exc_info.value)

    # Test uppercase characters
    with pytest.raises(CustomPineconeClientError) as exc_info:
        client.create_index("TestIndex")
    assert "letras minúsculas" in str(exc_info.value)


def test_create_index_error(client, mock_pinecone):
    """Test index creation with error."""
    mock_pinecone.create_index.side_effect = Exception("API Error")
    with pytest.raises(CustomPineconeClientError) as exc_info:
        client.create_index("test-index")
    assert "Erro ao criar a base de conhecimento" in str(exc_info.value)


def test_create_index_error_messages(client, mock_pinecone):
    """Test user-friendly error messages."""
    # Test 400 error
    mock_pinecone.create_index.side_effect = Exception("400 Bad Request")
    with pytest.raises(CustomPineconeClientError) as exc_info:
        client.create_index("test-index")
    assert "caracteres inválidos" in str(exc_info.value)

    # Test other errors
    mock_pinecone.create_index.side_effect = Exception("Unknown error")
    with pytest.raises(CustomPineconeClientError) as exc_info:
        client.create_index("test-index")
    assert "Por favor, tente novamente" in str(exc_info.value)


def test_delete_index(client, mock_pinecone):
    """Test successful index deletion."""
    mock_pinecone.delete_index.return_value = None
    assert client.delete_index("test-index") is True
    mock_pinecone.delete_index.assert_called_once_with("test-index")


def test_delete_index_error(client, mock_pinecone):
    """Test index deletion with error."""
    mock_pinecone.delete_index.side_effect = Exception("API Error")
    with pytest.raises(CustomPineconeClientError) as exc_info:
        client.delete_index("test-index")
    assert "Failed to delete index" in str(exc_info.value)


def test_list_indexes(client, mock_pinecone):
    """Test successful index listing."""
    mock_response = MagicMock()
    mock_response.names.return_value = ["index1", "index2"]
    mock_pinecone.list_indexes.return_value = mock_response
    indexes = client.list_indexes()
    assert indexes == ["index1", "index2"]
    mock_pinecone.list_indexes.assert_called_once()


def test_list_indexes_error(client, mock_pinecone):
    """Test index listing with error."""
    mock_pinecone.list_indexes.side_effect = Exception("API Error")
    with pytest.raises(CustomPineconeClientError) as exc_info:
        client.list_indexes()
    assert "Failed to list indexes" in str(exc_info.value)


def test_list_namespaces(client, mock_pinecone):
    """Test successful namespace listing."""
    # Mock the index instance
    mock_index = MagicMock()
    mock_index.describe_index_stats.return_value = {
        "namespaces": {"ns1": {}, "ns2": {}}
    }
    mock_pinecone.Index.return_value = mock_index

    namespaces = client.list_namespaces("test-index")
    assert sorted(namespaces) == ["ns1", "ns2"]
    mock_pinecone.Index.assert_called_once_with("test-index")


def test_list_namespaces_error(client, mock_pinecone):
    """Test namespace listing with error."""
    mock_pinecone.Index.side_effect = Exception("API Error")
    with pytest.raises(CustomPineconeClientError) as exc_info:
        client.list_namespaces("test-index")
    assert "Failed to list namespaces" in str(exc_info.value)


def test_delete_namespace(client, mock_pinecone):
    """Test successful namespace deletion."""
    # Mock the index instance
    mock_index = MagicMock()
    mock_index.delete = MagicMock(return_value=None)
    mock_pinecone.Index.return_value = mock_index

    assert client.delete_namespace("test-index", "test-namespace") is True
    mock_pinecone.Index.assert_called_once_with("test-index")
    mock_index.delete.assert_called_once_with(
        deleteAll=True, namespace="test-namespace"
    )


def test_delete_namespace_error(client, mock_pinecone):
    """Test namespace deletion with error."""
    mock_pinecone.Index.side_effect = Exception("API Error")
    with pytest.raises(CustomPineconeClientError) as exc_info:
        client.delete_namespace("test-index", "test-namespace")
    assert "Failed to delete namespace" in str(exc_info.value)


@pytest.mark.asyncio
async def test_upsert_vectors(client, mock_pinecone):
    """Test successful vector upsertion."""
    # Mock the index instance
    mock_index = MagicMock()
    mock_index.upsert = AsyncMock()
    mock_pinecone.Index.return_value = mock_index

    vectors = [
        {
            "id": "1",
            "values": [0.1, 0.2, 0.3],
            "metadata": {"key": "value"},
        }
    ]

    await client.upsert_vectors(
        index_name="test-index",
        vectors=vectors,
        namespace="test-namespace",
    )

    mock_pinecone.Index.assert_called_once_with("test-index")
    mock_index.upsert.assert_called_once_with(
        vectors=vectors,
        namespace="test-namespace",
    )


@pytest.mark.asyncio
async def test_upsert_vectors_error(client, mock_pinecone):
    """Test vector upsertion with error."""
    mock_pinecone.Index.side_effect = Exception("API Error")
    with pytest.raises(CustomPineconeClientError) as exc_info:
        await client.upsert_vectors(
            index_name="test-index",
            vectors=[],
            namespace="test-namespace",
        )
    assert "Failed to upsert vectors" in str(exc_info.value)
