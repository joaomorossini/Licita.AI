"""Chat com Edital interface module."""

import streamlit as st
from src.dify_client import upload_knowledge_file, chat_with_doc

# Define supported file types
SUPPORTED_TYPES = [
    "txt",
    "md",
    "markdown",
    "pdf",
    "html",
    "htm",
    "xlsx",
    "xls",
    "docx",
    "csv",
]
MAX_FILE_SIZE_MB = 15

# Configure page
st.set_page_config(
    page_title="Chat com Edital",
    layout="wide",
    initial_sidebar_state="expanded",
)


def chat_com_edital_page():
    """Display the Chat com Edital page with file upload and chat functionality.

    Returns:
        bool: True if the page loads successfully
    """
    st.header("Chat com Edital")

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "doc_id" not in st.session_state:
        st.session_state.doc_id = None

    if "upload_status" not in st.session_state:
        st.session_state.upload_status = None

    # File upload section with spinner and error handling
    uploaded_file = st.file_uploader(
        label="Upload Document",
        help=f"Supported formats: {', '.join(SUPPORTED_TYPES).upper()} • Max size: {MAX_FILE_SIZE_MB}MB",
        type=SUPPORTED_TYPES,
    )

    if (
        uploaded_file is not None
        and st.session_state.upload_status != uploaded_file.name
    ):
        # Check file size
        file_size_mb = uploaded_file.size / (1024 * 1024)  # Convert to MB
        if file_size_mb > MAX_FILE_SIZE_MB:
            st.error(
                f"❌ File too large! Maximum size is {MAX_FILE_SIZE_MB}MB. Your file is {file_size_mb:.1f}MB"
            )
            return False

        try:
            with st.spinner("Uploading document..."):
                # Upload file to Dify
                doc_id = upload_knowledge_file(
                    uploaded_file.getvalue(), uploaded_file.name
                )
                st.session_state.doc_id = doc_id
                st.session_state.upload_status = uploaded_file.name

                st.success(f"✅ Document uploaded successfully! Document ID: {doc_id}")
                st.info(
                    "⏳ The document is being processed. You can start chatting while it's being analyzed."
                )

        except Exception as e:
            st.error(f"❌ Error uploading document: {str(e)}")
            return False

    # Chat interface - always visible
    st.subheader("💬 Chat with the Assistant")

    if not st.session_state.messages:
        st.info(
            "👋 Hi! I'm your AI assistant. You can ask me anything, and if you upload a document, I'll help you analyze it."
        )

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Chat input
    if prompt := st.chat_input(
        "Ask me anything..."
        if not st.session_state.doc_id
        else "Ask about the document..."
    ):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.write(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = []

            try:
                for response_chunk in chat_with_doc(st.session_state.doc_id, prompt):
                    if response_chunk:  # Only process non-empty chunks
                        full_response.append(response_chunk)
                        # Show the response as it comes in
                        message_placeholder.markdown("".join(full_response))

                # Save the complete response
                final_response = "".join(full_response)
                if final_response:  # Only save if we got a response
                    st.session_state.messages.append(
                        {"role": "assistant", "content": final_response}
                    )
                else:
                    message_placeholder.error(
                        "❌ No response received from the assistant"
                    )

            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                message_placeholder.error(error_msg)
                # Add error message to chat history
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )
                # Log the error for debugging
                st.error(f"Detailed error: {str(e)}")

    return True
