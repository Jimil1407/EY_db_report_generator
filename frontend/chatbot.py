import streamlit as st
import requests
import json

# Backend API URL
BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="AI SQL Chatbot", layout="centered")

st.title("AI SQL Chatbot")

# User input for name and email
with st.sidebar:
    st.header("User Information")
    user_name = st.text_input("Your Name", "John Doe")
    user_email = st.text_input("Your Email", "john.doe@example.com")
    st.markdown("---")
    st.header("API Health Check")
    if st.button("Check Backend Health"):
        try:
            health_response = requests.get(f"{BACKEND_URL}/health")
            if health_response.status_code == 200:
                st.success(f"Backend is healthy! {health_response.json()}")
            else:
                st.error(f"Backend health check failed: {health_response.status_code} - {health_response.text}")
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the backend API. Make sure it is running.")
        except Exception as e:
            st.error(f"An error occurred during health check: {e}")

# Chatbot interface
st.header("Ask your SQL question")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Enter your question:"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Generating SQL query..."):
            try:
                # Prepare the payload
                payload = {
                    "user_name": user_name,
                    "user_email": user_email,
                    "query": prompt
                }
                headers = {"Content-Type": "application/json"}

                # Make the API call
                response = requests.post(
                    f"{BACKEND_URL}/generate-sql",
                    data=json.dumps(payload),
                    headers=headers
                )

                if response.status_code == 200:
                    data = response.json()
                    sql_query = data.get("sql_query", "No SQL query generated.")
                    st.code(sql_query, language="sql")
                    st.session_state.messages.append({"role": "assistant", "content": f"```sql\n{sql_query}\n```"})
                else:
                    error_message = f"Error: {response.status_code} - {response.text}"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
            except requests.exceptions.ConnectionError:
                error_message = "Could not connect to the backend API. Make sure it is running."
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
            except Exception as e:
                error_message = f"An error occurred: {e}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
