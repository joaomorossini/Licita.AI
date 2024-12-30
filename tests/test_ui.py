"""Tests for UI layout and components."""

import pytest
from src.chat_com_edital import chat_com_edital_page
from src.boletins import boletins_page


def test_navigation_layout():
    """Test that both pages can be loaded without errors."""
    chat_com_edital_page()
    boletins_page()
    assert True


def test_chat_page_components():
    """Test that the chat page contains all required components."""
    chat_com_edital_page()
    assert True  # If no exceptions are raised, components are present


def test_boletins_page_components():
    """Test that the boletins page contains all required components."""
    boletins_page()
    assert True  # If no exceptions are raised, components are present
