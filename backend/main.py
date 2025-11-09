"""
API Endpoints Testing Commands:

1. Health Check (GET):
   curl -X GET http://localhost:8000/health

2. Generate SQL (POST):
   curl -X POST http://localhost:8000/generate-sql \
     -H "Content-Type: application/json" \
     -d '{
       "user_name": "John Doe",
       "user_email": "john.doe@example.com",
       "query": "How many claims are pending?"
     }'

   Example with complex query:
   curl -X POST http://localhost:8000/generate-sql \
     -H "Content-Type: application/json" \
     -d '{
       "user_name": "Jane Smith",
       "user_email": "jane.smith@example.com",
       "query": "Show me all approved claims from last month with their amounts"
     }'
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import logging
import os
import re
from typing import Optional
import traceback
from pathlib import Path
from dotenv import load_dotenv # Re-enabling dotenv import

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load API key from .env.local file
env_path = Path(__file__).parent / ".env.local"
logger.info(f"Looking for .env.local file at: {env_path}")

if env_path.exists():
    logger.info(f".env.local file found at {env_path}")
    load_dotenv(dotenv_path=env_path)
    if os.getenv("GEMINI_API_KEY"):
        logger.info(f"API key loaded from .env.local: {os.getenv('GEMINI_API_KEY')[:10]}...")
    else:
        logger.error("GEMINI_API_KEY not found in .env.local file")
else:
    logger.error(f".env.local file not found at {env_path}")

# Initialize FastAPI app
app = FastAPI(
    title="AI Report Generator",
    description="AI-powered Medical Claims Analytics Bot - SQL Generation API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Few-shot examples for SQL generation
few_shots = [
    {
        "q": "How many claims are pending?",
        "a": "SELECT COUNT(*) FROM claims WHERE status = 'PENDING';",
    },
    {
        "q": "Show approved claims in last month.",
        "a": (
            "SELECT * FROM claims "
            "WHERE status = 'APPROVED' "
            "AND claim_date >= TRUNC(ADD_MONTHS(SYSDATE, -1), 'MM');"
        ),
    },
]

# Request/Response Models
class GenerateSQLRequest(BaseModel):
    name: str = Field(...)
    user_name: str = Field(...)
    user_email: str = Field(...)
    query: str = Field(...)
    

class GenerateSQLResponse(BaseModel):
    name:str = Field(...)
    sql_query: str = Field(...)
    status: str = Field(...)


# SQL Validation
def validate_sql(sql: str) -> tuple:
    """
    Validate that SQL is read-only (SELECT-only).
    Returns (is_valid, error_message)
    """
    if not sql or not sql.strip():
        return False, "SQL query is empty"
    
    sql_upper = sql.strip().upper()
    
    # Check if it starts with SELECT
    if not sql_upper.startswith("SELECT"):
        return False, "Only SELECT queries are allowed"
    
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


# Health Check Endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AI Report Generator"}


# Generate SQL Endpoint
@app.post("/generate-sql", response_model=GenerateSQLResponse)
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
        
        # Import here to avoid circular imports
        from backend.ai.sql_generator import SQLGenerator
        
        # Use the API key loaded at startup
        current_api_key = os.getenv("GEMINI_API_KEY") # Using os.getenv again
        if not current_api_key:
            logger.error("[API] GEMINI_API_KEY is not set in backend/.env.local file or environment")
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEY is not configured in backend/.env.local file or environment"
            )

        # Initialize SQL Generator with API key
        logger.info(f"[API] Initializing SQL Generator with API key: {current_api_key[:10]}...")
        sql_generator = SQLGenerator(few_shots=few_shots, api_key=current_api_key)
        
        # Generate SQL using AI
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
            sql_query=generated_sql,
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)