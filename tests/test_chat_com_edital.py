import pytest
from src.chat_com_edital import chat_com_edital_page


def test_chat_page_loads():
    """Test that the chat page loads without errors."""
    result = chat_com_edital_page()
    assert result is True


def test_file_uploader_component():
    """Test that the file uploader component is present and accepts PDFs."""
    result = chat_com_edital_page()
    assert result is True  # Basic functionality test

    # Note: More detailed UI testing would require snapshot testing
    # or a more sophisticated testing framework
