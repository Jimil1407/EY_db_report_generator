"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
from pathlib import Path

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure project root is on sys.path for flexible imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Ensure backend directory is on sys.path
backend_path = Path(__file__).resolve().parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Handle both relative and absolute imports
try:
    from .config import load_environment
    from .routes import health, query
except ImportError:
    # When running as script, use absolute imports
    from config import load_environment
    from routes import health, query

# Load environment variables
load_environment()

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

# Register routers
app.include_router(health.router)
app.include_router(query.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
