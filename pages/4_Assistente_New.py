import os
import requests
import streamlit as st
from dotenv import load_dotenv
import json

load_dotenv()

dify_api_key = os.getenv("DIFY_API_KEY")

url = "http://dify.cogmo.com.br/v1/chat-messages"

st.title("Dify Streamlit App")

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Enter you question")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        headers = {
            "Authorization": f"Bearer {dify_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "inputs": {},
            "query": prompt,
            "response_mode": "streaming",
            "conversation_id": st.session_state.conversation_id,
            "user": "aianytime",
            "files": [],
        }

        try:
            with requests.post(
                url, headers=headers, json=payload, stream=True
            ) as response:
                response.raise_for_status()
                full_response = ""

                for line in response.iter_lines():
                    if line:
                        line = line.decode("utf-8")
                        if line.startswith("data: "):
                            try:
                                event_data = json.loads(
                                    line[6:]
                                )  # Skip 'data: ' prefix
                                if event_data.get("event") == "agent_message":
                                    message_content = event_data.get("answer", "")
                                    if message_content:
                                        full_response += message_content
                                        message_placeholder.markdown(full_response)
                                elif event_data.get("event") == "message_end":
                                    st.session_state.conversation_id = event_data.get(
                                        "conversation_id",
                                        st.session_state.conversation_id,
                                    )
                            except json.JSONDecodeError:
                                continue

        except requests.exceptions.RequestException as e:
            st.error(f"Request error: {str(e)}")
            full_response = "An error occurred while making the request."

        message_placeholder.markdown(full_response)
        if full_response:  # Only append if we got a response
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )
