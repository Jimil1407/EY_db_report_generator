import streamlit as st
import requests
import json
import pandas as pd
import io
import base64

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

# Initialize PDF report storage
if "pdf_reports" not in st.session_state:
    st.session_state.pdf_reports = {}


def generate_pdf_report_for_message(message_idx: int) -> bool:
    """Generate a PDF report for the CSV data associated with a chat message."""
    csv_info = st.session_state.csv_data.get(message_idx)
    if not csv_info:
        return False
    
    csv_string = csv_info.get("csv_string")
    if not csv_string:
        csv_info["pdf_status"] = "error"
        csv_info["pdf_error"] = "Missing CSV data for PDF generation."
        return False
    
    # Avoid duplicate work if PDF already exists
    if st.session_state.pdf_reports.get(message_idx):
        csv_info["pdf_status"] = "ready"
        csv_info.pop("pdf_error", None)
        return True
    
    csv_info["pdf_status"] = "processing"
    pdf_payload = {
        "csv_data": csv_string,
        "title": csv_info.get("title") or f"Query Results {message_idx}",
        "report_description": csv_info.get("description"),
    }
    
    try:
        pdf_response = requests.post(
            f"{BACKEND_URL}/generate-pdf",
            data=json.dumps(pdf_payload),
            headers={"Content-Type": "application/json"},
            timeout=60,
        )
        if pdf_response.status_code != 200:
            csv_info["pdf_status"] = "error"
            csv_info["pdf_error"] = (
                f"PDF generation failed: {pdf_response.status_code} - {pdf_response.text}"
            )
            return False
        
        pdf_data = pdf_response.json()
        pdf_bytes = base64.b64decode(pdf_data.get("pdf_data", ""))
        st.session_state.pdf_reports[message_idx] = {
            "pdf_bytes": pdf_bytes,
            "file_name": pdf_data.get("file_name", f"query_results_{message_idx}.pdf"),
        }
        csv_info["pdf_status"] = "ready"
        csv_info.pop("pdf_error", None)
        return True
    
    except requests.exceptions.ConnectionError:
        csv_info["pdf_status"] = "error"
        csv_info["pdf_error"] = (
            "Could not connect to the backend API to generate PDF. Make sure it is running."
        )
    except Exception as e:
        csv_info["pdf_status"] = "error"
        csv_info["pdf_error"] = f"An error occurred while generating the PDF: {e}"
    
    return False

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
                st.dataframe(csv_info["preview_df"], width="stretch")

            # PDF generation controls
            pdf_info = st.session_state.pdf_reports.get(idx)
            pdf_status = csv_info.get("pdf_status")

            if pdf_status in (None, "pending"):
                csv_info["pdf_status"] = "pending"
                with st.spinner("Analyzing CSV and generating PDF report..."):
                    generate_pdf_report_for_message(idx)
                pdf_info = st.session_state.pdf_reports.get(idx)
                pdf_status = csv_info.get("pdf_status")

            if pdf_info:
                st.success("PDF report ready for download.")
                st.download_button(
                    label="Download PDF Report",
                    data=pdf_info["pdf_bytes"],
                    file_name=pdf_info["file_name"],
                    mime="application/pdf",
                    key=f"download_pdf_{idx}"
                )
            elif pdf_status == "processing":
                st.info("Generating PDF report...")
            elif pdf_status == "error":
                st.error(csv_info.get("pdf_error", "Failed to generate PDF report."))
                if st.button("Retry PDF generation", key=f"retry_pdf_{idx}"):
                    with st.spinner("Retrying PDF report generation..."):
                        generate_pdf_report_for_message(idx)
                        if st.session_state.pdf_reports.get(idx):
                            st.experimental_rerun()

# React to user input
if prompt := st.chat_input("Enter your question:"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        try:
            # Prepare the payload
            payload = {
                "user_name": user_name,
                "user_email": user_email,
                "query": prompt
            }
            headers = {"Content-Type": "application/json"}

            # Step 1: Show table selection status
            with st.spinner("Selecting tables..."):
                # Make the API call (this does both table selection and SQL generation)
                response = requests.post(
                    f"{BACKEND_URL}/generate-sql",
                    data=json.dumps(payload),
                    headers=headers
                )

            if response.status_code == 200:
                data = response.json()
                selected_tables = data.get("selected_tables", [])
                sql_query = data.get("sql_query", "No SQL query generated.")
                
                # Display selected tables
                if selected_tables:
                    st.success(f"**Selected tables:** {', '.join(selected_tables)}")
                
                # Step 2: Show SQL generation status (already done, but show for consistency)
                st.info("**Generating SQL query...**")
                
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
                                            "preview_df": df.head(5),
                                            "title": f"Query Results {message_idx}",
                                            "description": (
                                                f"Results generated for SQL query:\n{sql_query}\n\n"
                                                f"Original question: {prompt}\nRows returned: {row_count}"
                                            ),
                                            "sql_query": sql_query,
                                            "prompt": prompt,
                                            "pdf_status": "pending",
                                        }
                                        
                                        with st.spinner("Analyzing CSV results and generating PDF report..."):
                                            generate_pdf_report_for_message(message_idx)
                                        
                                        pdf_ready = (
                                            st.session_state.csv_data[message_idx].get("pdf_status") == "ready"
                                        )
                                        pdf_info = st.session_state.pdf_reports.get(message_idx)
                                        pdf_note = (
                                            " PDF report generated automatically."
                                            if pdf_ready
                                            else " PDF report will be available shortly."
                                        )
                                        
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
                                        st.dataframe(df.head(5), width="stretch")
                                        
                                        if pdf_ready and pdf_info:
                                            st.success("PDF report ready for download.")
                                            st.download_button(
                                                label="Download PDF Report",
                                                data=pdf_info["pdf_bytes"],
                                                file_name=pdf_info["file_name"],
                                                mime="application/pdf",
                                                key=f"download_pdf_new_{message_idx}"
                                            )
                                        
                                        # Store in session state
                                        tables_info = f"**Selected tables:** {', '.join(selected_tables)}\n\n" if selected_tables else ""
                                        st.session_state.messages.append({
                                            "role": "assistant", 
                                            "content": (
                                                f"{tables_info}```sql\n{sql_query}\n```\n\n"
                                                f"Query executed successfully. Returned {row_count} rows. "
                                                f"CSV download available.{pdf_note}"
                                            )
                                        })
                                    else:
                                        # Display all results in a table
                                        st.markdown(f"**Query Results ({row_count} rows):**")
                                        st.dataframe(df, width="stretch")
                                        
                                        # Also store CSV data for small results (optional download)
                                        message_idx = len(st.session_state.messages)
                                        csv_buffer = io.StringIO()
                                        df.to_csv(csv_buffer, index=False)
                                        csv_string = csv_buffer.getvalue()
                                        
                                        st.session_state.csv_data[message_idx] = {
                                            "csv_string": csv_string,
                                            "file_name": f"query_results_{message_idx}.csv",
                                            "row_count": row_count,
                                            "preview_df": None,
                                            "title": f"Query Results {message_idx}",
                                            "description": (
                                                f"Results generated for SQL query:\n{sql_query}\n\n"
                                                f"Original question: {prompt}\nRows returned: {row_count}"
                                            ),
                                            "sql_query": sql_query,
                                            "prompt": prompt,
                                            "pdf_status": "pending",
                                        }
                                        
                                        with st.spinner("Analyzing CSV results and generating PDF report..."):
                                            generate_pdf_report_for_message(message_idx)
                                        
                                        pdf_ready = (
                                            st.session_state.csv_data[message_idx].get("pdf_status") == "ready"
                                        )
                                        pdf_info = st.session_state.pdf_reports.get(message_idx)
                                        pdf_note = (
                                            " PDF report generated automatically."
                                            if pdf_ready
                                            else " PDF report will be available shortly."
                                        )
                                        
                                        # Store in session state
                                        tables_info = f"**Selected tables:** {', '.join(selected_tables)}\n\n" if selected_tables else ""
                                        st.session_state.messages.append({
                                            "role": "assistant", 
                                            "content": (
                                                f"{tables_info}```sql\n{sql_query}\n```\n\n"
                                                f"Query executed successfully. Returned {row_count} rows.{pdf_note}"
                                            )
                                        })
                                        
                                        if pdf_ready and pdf_info:
                                            st.success("PDF report ready for download.")
                                            st.download_button(
                                                label="Download PDF Report",
                                                data=pdf_info["pdf_bytes"],
                                                file_name=pdf_info["file_name"],
                                                mime="application/pdf",
                                                key=f"download_pdf_new_{message_idx}"
                                            )
                                else:
                                    st.info("Query executed successfully but returned no results.")
                                    tables_info = f"**Selected tables:** {', '.join(selected_tables)}\n\n" if selected_tables else ""
                                    st.session_state.messages.append({
                                        "role": "assistant", 
                                        "content": f"{tables_info}```sql\n{sql_query}\n```\n\nQuery executed successfully but returned no results."
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
