"""Tests for the boletins module."""

import pytest
from src.boletins import boletins_page


def test_boletins_page_loads():
    """Test that the boletins page loads without errors."""
    assert boletins_page() is True
