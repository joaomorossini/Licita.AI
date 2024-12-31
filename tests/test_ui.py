"""Tests for UI layout and components."""

import sys
from pathlib import Path
import pytest

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))


def test_pages_directory_structure():
    """Test that the pages directory exists and contains required files."""
    pages_dir = project_root / "pages"
    assert pages_dir.exists()
    assert pages_dir.is_dir()

    # Check that all required pages exist
    assert (pages_dir / "1_Assistente.py").exists()
    assert (pages_dir / "2_Boletins.py").exists()
    assert (pages_dir / "3_Dashboard.py").exists()


def test_assistente_ui_components():
    """Test that the Assistente page contains all required UI components."""
    page_path = project_root / "pages" / "1_Assistente.py"
    content = page_path.read_text()

    # Test UI components
    assert "st.title" in content
    assert "st.chat_input" in content
    assert "st.file_uploader" in content
    assert "st.sidebar" in content
    assert "st.container" in content
    assert "st.chat_message" in content


def test_boletins_ui_components():
    """Test that the Boletins page contains all required UI components."""
    page_path = project_root / "pages" / "2_Boletins.py"
    content = page_path.read_text()

    # Test UI components
    assert "st.title" in content
    assert "st.date_input" in content
    assert "st.dataframe" in content
    assert "st.columns" in content
    assert "st.subheader" in content


def test_dashboard_ui_components():
    """Test that the Dashboard page contains all required UI components."""
    page_path = project_root / "pages" / "3_Dashboard.py"
    content = page_path.read_text()

    # Test UI components
    assert "st.title" in content
    assert "st.markdown" in content
    assert "st.info" in content  # For the "in development" message
