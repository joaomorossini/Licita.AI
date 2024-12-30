import pytest
from src.main import app_function


def test_streamlit_runs():
    """Test that the Streamlit app function can be called without errors."""
    assert callable(app_function)
    result = app_function()
    assert result is True
