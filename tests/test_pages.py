"""Tests for Streamlit pages."""

import sys
from pathlib import Path
import pytest
import streamlit as st

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))


def test_home_page_exists():
    """Test that the home page file exists."""
    home_path = project_root / "Home.py"
    assert home_path.exists()
    assert home_path.is_file()


def test_assistente_page_exists():
    """Test that the Assistente page exists and has required components."""
    page_path = project_root / "pages" / "1_Assistente.py"
    assert page_path.exists()
    assert page_path.is_file()

    # Read the file content to check for required components
    content = page_path.read_text()
    assert "SUPPORTED_TYPES" in content
    assert "MAX_FILE_SIZE_MB" in content
    assert "st.set_page_config" in content
    assert 'page_icon="📄"' in content


def test_boletins_page_exists():
    """Test that the Boletins page exists and has required components."""
    page_path = project_root / "pages" / "2_Boletins.py"
    assert page_path.exists()
    assert page_path.is_file()

    # Read the file content to check for required components
    content = page_path.read_text()
    assert "data = {" in content
    assert '"Número"' in content
    assert '"Cliente"' in content
    assert '"Recebido em"' in content
    assert "st.set_page_config" in content
    assert 'page_title="Boletins - Licita.AI"' in content
    assert 'page_icon="📰"' in content


def test_dashboard_page_exists():
    """Test that the Dashboard page exists and has required components."""
    page_path = project_root / "pages" / "3_Dashboard.py"
    assert page_path.exists()
    assert page_path.is_file()

    # Read the file content to check for required components
    content = page_path.read_text()
    assert "st.set_page_config" in content
    assert 'page_title="Dashboard - Licita.AI"' in content
    assert 'page_icon="📊"' in content
