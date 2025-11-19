"""
Query-related endpoints for SQL generation and execution.
"""
from fastapi import APIRouter, HTTPException
import logging
import sys
from pathlib import Path
import traceback

# Handle both relative and absolute imports
try:
    from ..models import GenerateSQLRequest, GenerateSQLResponse, ExecuteQueryRequest, ExecuteQueryResponse
    from ..config import get_gemini_api_key, FEW_SHOT_EXAMPLES
    from ..utils.validation import validate_sql
except ImportError:
    # When running as script, try different import paths
    try:
        from backend.models import GenerateSQLRequest, GenerateSQLResponse, ExecuteQueryRequest, ExecuteQueryResponse
        from backend.config import get_gemini_api_key, FEW_SHOT_EXAMPLES
        from backend.utils.validation import validate_sql
    except ImportError:
        # When running from backend directory directly
        from models import GenerateSQLRequest, GenerateSQLResponse, ExecuteQueryRequest, ExecuteQueryResponse
        from config import get_gemini_api_key, FEW_SHOT_EXAMPLES
        from utils.validation import validate_sql

logger = logging.getLogger(__name__)

# Ensure project root is on sys.path for flexible imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

router = APIRouter()


@router.post("/generate-sql", response_model=GenerateSQLResponse)
async def generate_sql(request: GenerateSQLRequest):
    """
    Generate SQL query from natural language query.
    
    Request body:
    - user_name: Name of the user making the request
    - user_email: Email of the user making the request
    - query: Natural language query/question
    
    Response:
    - sql_query: Generated SQL query
    - status: Success or error status
    """
    try:
        logger.info(f"[API] generate-sql: Processing query '{request.query}' with user_email {request.user_email}")
        
        # Import here to avoid circular imports; support both package and script runs
        try:
            from ..ai.sql_generator import SQLGenerator
            from ..ai.table_selector import TableSelector
        except ImportError:
            try:
                from backend.ai.sql_generator import SQLGenerator
                from backend.ai.table_selector import TableSelector
            except ImportError:
                try:
                    from ai.sql_generator import SQLGenerator
                    from ai.table_selector import TableSelector
                except ImportError:
                    # Last resort - direct import
                    import sys
                    from pathlib import Path
                    backend_path = Path(__file__).resolve().parent.parent
                    if str(backend_path) not in sys.path:
                        sys.path.insert(0, str(backend_path))
                    from ai.sql_generator import SQLGenerator
                    from ai.table_selector import TableSelector
        
        # Get API key
        try:
            current_api_key = get_gemini_api_key()
        except ValueError as e:
            logger.error(f"[API] {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )

        # Step 1: Select relevant tables using Gemini
        logger.info(f"[API] generate-sql: Selecting relevant tables for query with user_email {request.user_email}")
        table_selector = TableSelector(api_key=current_api_key)
        selected_tables = table_selector.select_tables(request.query)
        logger.info(f"[API] generate-sql: Selected tables: {selected_tables} with user_email {request.user_email}")

        # Step 2: Initialize SQL Generator with selected tables
        logger.info(f"[API] Initializing SQL Generator with API key: {current_api_key[:10]}... and selected tables: {selected_tables}")
        sql_generator = SQLGenerator(
            few_shots=FEW_SHOT_EXAMPLES, 
            api_key=current_api_key,
            selected_tables=selected_tables
        )
        
        # Step 3: Generate SQL using AI with filtered schema
        generated_sql = sql_generator.generate_query(request.query)
        
        # Validate SQL is read-only
        is_valid, error_message = validate_sql(generated_sql)
        
        if not is_valid:
            logger.warning(f"[API] generate-sql: Validation failed - {error_message} with user_email {request.user_email}")
            raise HTTPException(
                status_code=400,
                detail=f"Generated SQL failed validation: {error_message}"
            )
        
        logger.info(f"[API] generate-sql: Successfully generated SQL with user_email {request.user_email}")
        
        return GenerateSQLResponse(
            user_name=request.user_name,
            user_email=request.user_email,
            sql_query=generated_sql,
            selected_tables=selected_tables,
            status="success"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] generate-sql: Error - {str(e)} with user_email {request.user_email}")
        logger.error(f"[API] generate-sql: Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/execute-query", response_model=ExecuteQueryResponse)
async def execute_query(request: ExecuteQueryRequest):
    """
    Execute a SQL query and return results.
    
    Request body:
    - sql_query: SQL query to execute
    
    Response:
    - results: List of dictionaries containing query results
    - columns: List of column names
    - row_count: Number of rows returned
    - error: Error message if execution failed
    - status: Success or error status
    """
    try:
        logger.info(f"[API] execute-query: Executing SQL query")
        
        # Validate SQL is read-only
        is_valid, error_message = validate_sql(request.sql_query)
        
        if not is_valid:
            logger.warning(f"[API] execute-query: Validation failed - {error_message}")
            raise HTTPException(
                status_code=400,
                detail=f"SQL query failed validation: {error_message}"
            )
        
        # Import query executor from connection module
        try:
            from ..database.connection import execute_query_with_count
        except ImportError:
            try:
                from backend.database.connection import execute_query_with_count
            except ImportError:
                try:
                    from database.connection import execute_query_with_count
                except ImportError:
                    # Last resort - direct import
                    import sys
                    from pathlib import Path
                    backend_path = Path(__file__).resolve().parent.parent
                    if str(backend_path) not in sys.path:
                        sys.path.insert(0, str(backend_path))
                    from database.connection import execute_query_with_count
        
        # Execute the query
        results, columns, row_count, error = execute_query_with_count(request.sql_query)
        
        if error:
            logger.error(f"[API] execute-query: Query execution failed - {error}")
            return ExecuteQueryResponse(
                results=[],
                columns=[],
                row_count=0,
                error=error,
                status="error"
            )
        
        logger.info(f"[API] execute-query: Successfully executed query. Returned {row_count} rows.")
        
        return ExecuteQueryResponse(
            results=results,
            columns=columns,
            row_count=row_count,
            error=None,
            status="success"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] execute-query: Error - {str(e)}")
        logger.error(f"[API] execute-query: Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

