import streamlit as st
import requests
import json
import pandas as pd
import io

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

# Initialize CSV data storage
if "csv_data" not in st.session_state:
    st.session_state.csv_data = {}

# Display chat messages from history on app rerun
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # If this message has associated CSV data, show download button
        if idx in st.session_state.csv_data:
            csv_info = st.session_state.csv_data[idx]
            st.info(f"Query returned {csv_info['row_count']} rows. Download the CSV file below:")
            st.download_button(
                label="Download Results as CSV",
                data=csv_info["csv_string"],
                file_name=csv_info["file_name"],
                mime="text/csv",
                key=f"download_{idx}"  # Unique key for each download button
            )
            
            # Show preview if available
            if csv_info.get("preview_df") is not None:
                st.markdown("**Preview (first 5 rows):**")
                st.dataframe(csv_info["preview_df"], use_container_width=True)

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
                    
                    # Display the SQL query
                    st.code(sql_query, language="sql")
                    
                    # Execute the query
                    with st.spinner("Executing query..."):
                        try:
                            execute_payload = {"sql_query": sql_query}
                            execute_response = requests.post(
                                f"{BACKEND_URL}/execute-query",
                                data=json.dumps(execute_payload),
                                headers=headers
                            )
                            
                            if execute_response.status_code == 200:
                                execute_data = execute_response.json()
                                
                                if execute_data.get("status") == "success":
                                    results = execute_data.get("results", [])
                                    columns = execute_data.get("columns", [])
                                    row_count = execute_data.get("row_count", 0)
                                    
                                    if row_count > 0:
                                        # Convert results to DataFrame
                                        df = pd.DataFrame(results)
                                        
                                        # Check if more than 5 rows
                                        if row_count > 5:
                                            # Prepare CSV download
                                            csv_buffer = io.StringIO()
                                            df.to_csv(csv_buffer, index=False)
                                            csv_string = csv_buffer.getvalue()
                                            
                                            # Get the index for this message (will be the next index)
                                            message_idx = len(st.session_state.messages)
                                            
                                            # Store CSV data in session state
                                            st.session_state.csv_data[message_idx] = {
                                                "csv_string": csv_string,
                                                "file_name": f"query_results_{message_idx}.csv",
                                                "row_count": row_count,
                                                "preview_df": df.head(5)
                                            }
                                            
                                            st.info(f"Query returned {row_count} rows. Download the CSV file below:")
                                            st.download_button(
                                                label="Download Results as CSV",
                                                data=csv_string,
                                                file_name=f"query_results_{message_idx}.csv",
                                                mime="text/csv",
                                                key=f"download_new_{message_idx}"
                                            )
                                            
                                            # Show first 5 rows as preview
                                            st.markdown("**Preview (first 5 rows):**")
                                            st.dataframe(df.head(5), use_container_width=True)
                                            
                                            # Store in session state
                                            st.session_state.messages.append({
                                                "role": "assistant", 
                                                "content": f"```sql\n{sql_query}\n```\n\nQuery executed successfully. Returned {row_count} rows. CSV download available."
                                            })
                                        else:
                                            # Display all results in a table
                                            st.markdown(f"**Query Results ({row_count} rows):**")
                                            st.dataframe(df, use_container_width=True)
                                            
                                            # Also store CSV data for small results (optional download)
                                            message_idx = len(st.session_state.messages)
                                            csv_buffer = io.StringIO()
                                            df.to_csv(csv_buffer, index=False)
                                            csv_string = csv_buffer.getvalue()
                                            
                                            st.session_state.csv_data[message_idx] = {
                                                "csv_string": csv_string,
                                                "file_name": f"query_results_{message_idx}.csv",
                                                "row_count": row_count,
                                                "preview_df": None
                                            }
                                            
                                            # Store in session state
                                            st.session_state.messages.append({
                                                "role": "assistant", 
                                                "content": f"```sql\n{sql_query}\n```\n\nQuery executed successfully. Returned {row_count} rows."
                                            })
                                    else:
                                        st.info("Query executed successfully but returned no results.")
                                        st.session_state.messages.append({
                                            "role": "assistant", 
                                            "content": f"```sql\n{sql_query}\n```\n\nQuery executed successfully but returned no results."
                                        })
                                else:
                                    error_msg = execute_data.get("error", "Unknown error occurred")
                                    st.error(f"Query execution failed: {error_msg}")
                                    st.session_state.messages.append({
                                        "role": "assistant", 
                                        "content": f"```sql\n{sql_query}\n```\n\nError: {error_msg}"
                                    })
                            else:
                                error_message = f"Error executing query: {execute_response.status_code} - {execute_response.text}"
                                st.error(error_message)
                                st.session_state.messages.append({
                                    "role": "assistant", 
                                    "content": f"```sql\n{sql_query}\n```\n\n{error_message}"
                                })
                        except requests.exceptions.ConnectionError:
                            error_message = "Could not connect to the backend API to execute query. Make sure it is running."
                            st.error(error_message)
                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": f"```sql\n{sql_query}\n```\n\n{error_message}"
                            })
                        except Exception as e:
                            error_message = f"An error occurred while executing query: {e}"
                            st.error(error_message)
                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": f"```sql\n{sql_query}\n```\n\n{error_message}"
                            })
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
