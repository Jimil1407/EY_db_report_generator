from dotenv import load_dotenv
import os
import cx_Oracle
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Tuple
import logging
from pathlib import Path

# Try to load .env file from multiple locations
env_files = [
    Path(__file__).parent.parent / ".env",  # backend/.env
    Path(__file__).parent.parent / ".env.local",  # backend/.env.local
    Path(__file__).parent.parent.parent / ".env",  # project root .env
]

env_loaded = False
for env_file in env_files:
    if env_file.exists():
        load_dotenv(dotenv_path=env_file)
        logger_temp = logging.getLogger(__name__)
        logger_temp.info(f"Loaded environment variables from {env_file}")
        env_loaded = True
        break

if not env_loaded:
    # Fallback to default load_dotenv behavior
    load_dotenv()
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("No .env file found in expected locations, using default load_dotenv()")

logger = logging.getLogger(__name__)


def get_db_connection():
    """
    Create and return a database connection.
    Returns a cx_Oracle connection object.
    
    Supports both JDBC URL format and separate host/port/service format.
    JDBC URL format: jdbc:oracle:thin:@host:port:service or jdbc:oracle:thin:@host:port/service
    """
    import re
    
    jdbc_url = os.getenv("ORACLE_JDBC_URL")
    username = os.getenv("ORACLE_USER")
    password = os.getenv("ORACLE_PASSWORD")
    port = os.getenv("PORT")
    service_name = os.getenv("SERVICE")
    
    # Check for missing environment variables
    missing_vars = []
    if not jdbc_url:
        missing_vars.append("ORACLE_JDBC_URL")
    if not username:
        missing_vars.append("ORACLE_USER")
    if not password:
        missing_vars.append("ORACLE_PASSWORD")
    
    if missing_vars:
        error_msg = f"Missing required database environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Parse JDBC URL if it's in JDBC format
    host = None
    parsed_port = None
    parsed_service = None
    
    if jdbc_url.startswith("jdbc:oracle:thin:@"):
        # Parse JDBC URL: jdbc:oracle:thin:@host:port:service or jdbc:oracle:thin:@host:port/service
        jdbc_url_clean = jdbc_url.replace("jdbc:oracle:thin:@", "")
        
        # Try format: host:port:service
        if ":" in jdbc_url_clean and jdbc_url_clean.count(":") >= 2:
            parts = jdbc_url_clean.split(":")
            if len(parts) >= 3:
                host = parts[0]
                parsed_port = parts[1]
                parsed_service = ":".join(parts[2:])  # In case service has colons
        # Try format: host:port/service
        elif "/" in jdbc_url_clean:
            parts = jdbc_url_clean.split("/")
            if len(parts) == 2:
                host_port = parts[0]
                parsed_service = parts[1]
                if ":" in host_port:
                    host, parsed_port = host_port.split(":", 1)
        # Try format: host:port (service from env)
        elif ":" in jdbc_url_clean:
            parts = jdbc_url_clean.split(":")
            if len(parts) >= 2:
                host = parts[0]
                parsed_port = parts[1]
        
        logger.info(f"Parsed JDBC URL - Host: {host}, Port: {parsed_port}, Service: {parsed_service}")
    
    # Use parsed values if available, otherwise use environment variables
    final_host = host if host else jdbc_url
    final_port = parsed_port if parsed_port else port
    final_service = parsed_service if parsed_service else service_name
    
    # Validate we have all required components
    if not final_host:
        raise ValueError("Could not determine database host from ORACLE_JDBC_URL")
    if not final_port:
        raise ValueError("Could not determine database port. Set PORT environment variable or use JDBC URL format")
    if not final_service:
        raise ValueError("Could not determine service name. Set SERVICE environment variable or use JDBC URL format")
    
    try:
        # Log connection attempt (without sensitive data)
        logger.info(f"Attempting to connect to Oracle database at {final_host}:{final_port}/{final_service} as user {username}")
        
        dsn = cx_Oracle.makedsn(final_host, final_port, service_name=final_service)
        logger.debug(f"DSN created: {dsn}")
        
        connection = cx_Oracle.connect(username, password, dsn)
        logger.info("Database connection established successfully")
        return connection
    except cx_Oracle.DatabaseError as e:
        error_msg = f"Database connection failed: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Connection details - Host: {final_host}, Port: {final_port}, Service: {final_service}, User: {username}")
        raise
    except Exception as e:
        error_msg = f"Unexpected error during database connection: {str(e)}"
        logger.error(error_msg)
        raise


@contextmanager
def get_db_cursor():
    """
    Context manager for database cursor.
    Automatically handles connection cleanup.
    
    Usage:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM table")
            results = cursor.fetchall()
    """
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        yield cursor
        connection.commit()
    except Exception as e:
        if connection:
            connection.rollback()
        raise e
    finally:
        if connection:
            connection.close()


def _clean_sql_query(sql_query: str) -> str:
    """
    Clean SQL query by removing trailing semicolons and extra whitespace.
    Oracle's cursor.execute() doesn't accept semicolons.
    """
    if not sql_query:
        return sql_query
    
    cleaned = sql_query.strip()
    # Remove trailing semicolon(s)
    while cleaned.endswith(';'):
        cleaned = cleaned[:-1].strip()
    
    return cleaned


def execute_query(sql_query: str, max_rows: Optional[int] = None) -> Tuple[List[Dict[str, Any]], List[str], Optional[str]]:
    """
    Execute a SQL query and return results.
    
    Args:
        sql_query: SQL query string to execute
        max_rows: Maximum number of rows to fetch (None for all rows)
    
    Returns:
        Tuple of:
        - results: List of dictionaries, each representing a row
        - columns: List of column names
        - error: Error message if execution failed, None otherwise
    
    Example:
        results, columns, error = execute_query("SELECT * FROM table WHERE id = 1")
        if error:
            print(f"Error: {error}")
        else:
            print(f"Columns: {columns}")
            print(f"Results: {results}")
    """
    try:
        # Clean the SQL query (remove semicolons, etc.)
        cleaned_sql = _clean_sql_query(sql_query)
        logger.debug(f"Executing SQL query: {cleaned_sql[:100]}...")
        
        with get_db_cursor() as cursor:
            # Execute the query
            cursor.execute(cleaned_sql)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Fetch results
            if max_rows:
                rows = cursor.fetchmany(max_rows)
            else:
                rows = cursor.fetchall()
            
            # Convert rows to list of dictionaries
            results = []
            for row in rows:
                row_dict = {}
                for i, col_name in enumerate(columns):
                    # Handle Oracle-specific types
                    value = row[i]
                    # Check for LOB type
                    try:
                        if hasattr(value, 'read') and hasattr(value, 'size'):
                            # It's likely a LOB type
                            value = value.read()
                    except (AttributeError, TypeError):
                        pass
                    
                    # Convert datetime/timestamp objects to string
                    if value is not None:
                        type_name = type(value).__name__
                        if 'datetime' in type_name.lower() or 'timestamp' in type_name.lower() or 'date' in type_name.lower():
                            value = str(value)
                    
                    row_dict[col_name] = value
                results.append(row_dict)
            
            logger.info(f"Query executed successfully. Returned {len(results)} rows.")
            return results, columns, None
            
    except cx_Oracle.DatabaseError as e:
        error_msg = f"Database error: {str(e)}"
        logger.error(f"Query execution failed: {error_msg}")
        return [], [], error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"Query execution failed: {error_msg}")
        return [], [], error_msg


def execute_query_with_count(sql_query: str) -> Tuple[List[Dict[str, Any]], List[str], int, Optional[str]]:
    """
    Execute a SQL query and return results along with total row count.
    
    Args:
        sql_query: SQL query string to execute
    
    Returns:
        Tuple of:
        - results: List of dictionaries, each representing a row
        - columns: List of column names
        - total_count: Total number of rows (may be limited by fetch)
        - error: Error message if execution failed, None otherwise
    """
    try:
        # Clean the SQL query (remove semicolons, etc.)
        cleaned_sql = _clean_sql_query(sql_query)
        logger.debug(f"Executing SQL query: {cleaned_sql[:100]}...")
        
        with get_db_cursor() as cursor:
            # Execute the query
            cursor.execute(cleaned_sql)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Fetch all results
            rows = cursor.fetchall()
            total_count = len(rows)
            
            # Convert rows to list of dictionaries
            results = []
            for row in rows:
                row_dict = {}
                for i, col_name in enumerate(columns):
                    # Handle Oracle-specific types
                    value = row[i]
                    # Check for LOB type
                    try:
                        if hasattr(value, 'read') and hasattr(value, 'size'):
                            # It's likely a LOB type
                            value = value.read()
                    except (AttributeError, TypeError):
                        pass
                    
                    # Convert datetime/timestamp objects to string
                    if value is not None:
                        type_name = type(value).__name__
                        if 'datetime' in type_name.lower() or 'timestamp' in type_name.lower() or 'date' in type_name.lower():
                            value = str(value)
                    
                    row_dict[col_name] = value
                results.append(row_dict)
            
            logger.info(f"Query executed successfully. Returned {total_count} rows.")
            return results, columns, total_count, None
            
    except cx_Oracle.DatabaseError as e:
        error_msg = f"Database error: {str(e)}"
        logger.error(f"Query execution failed: {error_msg}")
        return [], [], 0, error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"Query execution failed: {error_msg}")
        return [], [], 0, error_msg


# Keep the original test code for backward compatibility
if __name__ == "__main__":
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM ASRIT_PATIENT WHERE ROWNUM = 1")
            result = cursor.fetchone()
            print("Connection successful!")
            print("Sample query result:", result)
    except cx_Oracle.DatabaseError as e:
        print("Database connection or query failed:", e)
