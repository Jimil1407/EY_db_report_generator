"""
SQL validation utilities.
"""
import re


def validate_sql(sql: str) -> tuple:
    """
    Validate that SQL is read-only (SELECT-only).
    Returns (is_valid, error_message)
    """
    if not sql or not sql.strip():
        return False, "SQL query is empty"
    
    sql_upper = sql.strip().upper()
    
    # List of dangerous keywords that should not be present
    dangerous_keywords = [
        "INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE", 
        "ALTER", "CREATE", "EXEC", "EXECUTE", "CALL",
        "MERGE", "GRANT", "REVOKE", "COMMIT", "ROLLBACK"
    ]
    
    for keyword in dangerous_keywords:
        # Use word boundary to avoid false positives (e.g., "SELECT" in "SELECTION")
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, sql_upper):
            return False, f"Dangerous keyword '{keyword}' detected. Only SELECT queries are allowed"
    
    return True, None

