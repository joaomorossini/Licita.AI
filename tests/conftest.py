"""Test configuration and fixtures."""

import pytest
import streamlit as st


@pytest.fixture(autouse=True)
def mock_streamlit_session():
    """Mock Streamlit's session state for testing."""
    # Clear session state before each test
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    # Initialize basic session state
    st.session_state.page_title = ""
    st.session_state.page_icon = ""

    yield

    # Clean up after test
    for key in list(st.session_state.keys()):
        del st.session_state[key]
