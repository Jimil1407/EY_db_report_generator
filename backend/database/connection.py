from dotenv import load_dotenv
import os
import oracledb
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Tuple
import logging
from pathlib import Path

# Try to load .env files from multiple locations
# Priority: .env.local (local overrides) > .env (default) > project root .env
# Load both .env and .env.local if they exist, with .env.local taking precedence
env_files_priority = [
    Path(__file__).parent.parent / ".env",  # backend/.env (base config)
    Path(__file__).parent.parent / ".env.local",  # backend/.env.local (local overrides - highest priority)
    Path(__file__).parent.parent.parent / ".env",  # project root .env (fallback)
]

env_loaded = False
loaded_files = []

# Load all existing env files in order (later files override earlier ones)
for env_file in env_files_priority:
    if env_file.exists():
        load_dotenv(dotenv_path=env_file, override=True)  # override=True ensures .env.local overrides .env
        loaded_files.append(env_file)
        env_loaded = True

if env_loaded:
    logger_temp = logging.getLogger(__name__)
    logger_temp.info(f"Loaded environment variables from: {', '.join(str(f) for f in loaded_files)}")
    if Path(__file__).parent.parent / ".env.local" in loaded_files:
        logger_temp.info("Using .env.local for local configuration overrides")
else:
    # Fallback to default load_dotenv behavior
    load_dotenv()
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("No .env file found in expected locations, using default load_dotenv()")

logger = logging.getLogger(__name__)


def get_db_connection():
    """
    Create and return a database connection.
    Returns an oracledb connection object.
    
    Supports both JDBC URL format and separate host/port/service format.
    JDBC URL format: jdbc:oracle:thin:@host:port:service or jdbc:oracle:thin:@host:port/service
    """
    import re
    
    jdbc_url = os.getenv("ORACLE_JDBC_URL")
    username = os.getenv("ORACLE_USER")
    password = os.getenv("ORACLE_PASSWORD")
    port = os.getenv("PORT")
    service_name = os.getenv("SERVICE")
    
    # Debug: Log which variables are loaded (without sensitive values)
    logger.debug(f"Environment variables loaded - ORACLE_JDBC_URL: {'SET' if jdbc_url else 'NOT SET'}, "
                 f"ORACLE_USER: {'SET' if username else 'NOT SET'}, "
                 f"ORACLE_PASSWORD: {'SET' if password else 'NOT SET'}, "
                 f"PORT: {port if port else 'NOT SET'}, "
                 f"SERVICE: {service_name if service_name else 'NOT SET'}")
    
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
        logger.error("Please check your .env.local file in the backend directory")
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
        
        # Quick network connectivity test before attempting Oracle connection
        import socket
        try:
            logger.debug(f"Testing network connectivity to {final_host}:{final_port}...")
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(5)  # 5 second timeout for connectivity test
            result = test_socket.connect_ex((final_host, int(final_port)))
            test_socket.close()
            if result != 0:
                logger.warning(f"Network connectivity test failed - port {final_port} on {final_host} is not reachable")
                logger.warning("This suggests a network/firewall issue, not a database authentication issue")
            else:
                logger.debug(f"Network connectivity test passed - port {final_port} is reachable")
        except Exception as net_err:
            logger.warning(f"Network connectivity test error: {net_err}")
        
        # Create DSN with connection timeout configuration
        # Note: python-oracledb doesn't support timeout in connect(), but we can set it in DSN
        # Connection timeout is typically handled at the network level
        dsn = oracledb.makedsn(
            host=final_host, 
            port=final_port, 
            service_name=final_service
        )
        logger.debug(f"DSN created: {dsn}")
        
        # Attempt connection
        # Note: If connection times out, it's likely a network/firewall issue
        # Check: VPN connection, security groups, network access
        connection = oracledb.connect(
            user=username, 
            password=password, 
            dsn=dsn
        )
        logger.info("Database connection established successfully")
        return connection
    except oracledb.DatabaseError as e:
        error_msg = f"Database connection failed: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Connection details - Host: {final_host}, Port: {final_port}, Service: {final_service}, User: {username}")
        
        # Provide troubleshooting hints for common timeout issues
        if "timed out" in str(e).lower() or "timeout" in str(e).lower():
            logger.error("=" * 60)
            logger.error("TROUBLESHOOTING: Connection timeout detected")
            logger.error("=" * 60)
            logger.error("Since this was working yesterday, likely causes:")
            logger.error("  1. Your IP address changed (if using dynamic IP)")
            logger.error("     → Check your current IP and verify it's in AWS Security Group")
            logger.error("  2. AWS Security Group rules changed")
            logger.error("     → Your IP may have been removed from allowed list")
            logger.error("  3. Network routing/firewall changes")
            logger.error("     → Corporate firewall or ISP may have changed rules")
            logger.error("")
            logger.error("Quick tests to run:")
            logger.error("  PowerShell: Test-NetConnection -ComputerName {} -Port {}".format(final_host, final_port))
            logger.error("  Or: telnet {} {}".format(final_host, final_port))
            logger.error("")
            logger.error("If network test fails, contact your DBA/DevOps team to:")
            logger.error("  - Verify your current IP is in RDS Security Group")
            logger.error("  - Check if RDS instance is running and accessible")
            logger.error("=" * 60)
        
        raise
    except Exception as e:
        error_msg = f"Unexpected error during database connection: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Connection details - Host: {final_host}, Port: {final_port}, Service: {final_service}, User: {username}")
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
            
    except oracledb.DatabaseError as e:
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
            
    except oracledb.DatabaseError as e:
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
    except oracledb.DatabaseError as e:
        print("Database connection or query failed:", e)
