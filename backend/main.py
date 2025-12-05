"""
Multi-Agent PDF Intelligence + Language Learning Platform
FastAPI Backend Main Application

Author: Santosh Yadav
Date: November 2025
"""

import os
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn
from sqlalchemy.exc import SQLAlchemyError

from models.database import init_db, get_db_session, engine
from config.gemini_config import GeminiClient
from routes.api import router as api_router
from middleware.error_handler import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)

# Setup structured JSON logging for Cloud Run
# Minimal JSON logger to avoid external dependency
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log = {
            "level": record.levelname,
            "time": datetime.utcnow().isoformat(),
            "message": record.getMessage(),
            "logger": record.name,
        }
        if hasattr(record, 'request_id'):
            log['request_id'] = getattr(record, 'request_id')
        if record.exc_info:
            log['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(log)

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
# Avoid adding duplicate handlers
if not root_logger.handlers:
    root_logger.addHandler(handler)

logger = logging.getLogger(__name__)

# Global instances
vector_store = None
gemini_client: GeminiClient = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Initializes database, vector store, and Gemini client on startup.
    """
    global vector_store, gemini_client

    logger.info("Starting Multi-Agent PDF Intelligence Platform...")

    # Degraded mode: skip heavy initializations to allow quick boot
    degraded_mode = os.getenv("DEGRADED_MODE", "false").lower() in {"1", "true", "yes"}

    try:
        if not degraded_mode:
            # Initialize database
            logger.info("Initializing database connection...")
            init_db()
            logger.info("Database initialized successfully")
        else:
            logger.warning("DEGRADED_MODE enabled: Skipping database initialization")

        # Initialize Chroma Vector Store (only if not in degraded mode)
        vector_store = None
        if not degraded_mode:
            try:
                logger.info("Initializing Chroma Vector Store...")
                persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
                os.makedirs(persist_dir, exist_ok=True)
                # Runtime import to avoid importing chromadb unless needed
                from storage.vector_store import ChromaVectorStore
                vector_store = ChromaVectorStore(persist_directory=persist_dir)
                logger.info(f"Vector store initialized at {persist_dir}")
            except Exception as ve:
                logger.warning(f"Vector store initialization failed: {ve}. Continuing without vector search capabilities.")
        else:
            logger.warning("DEGRADED_MODE enabled: Skipping vector store initialization")

        # Initialize Gemini API Client (optional in degraded)
        gemini_client = None
        try:
            logger.info("Initializing Gemini API Client...")
            gemini_client = GeminiClient()
            logger.info("Gemini client initialized successfully")
        except Exception as ge:
            logger.warning(f"Gemini client initialization failed: {ge}")
            if not degraded_mode:
                raise

        # Store in app state
        app.state.vector_store = vector_store
        app.state.gemini_client = gemini_client

        logger.info("✅ All services initialization step completed")

    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {str(e)}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Shutting down application...")
    try:
        if engine:
            engine.dispose()
            logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent PDF Intelligence + Language Learning Platform",
    description="""
    Production-ready AI-powered platform for PDF-based language learning.

    Features:
    - 7 Specialized AI Agents (Gemini-powered)
    - Intelligent PDF Processing & Topic Extraction
    - Contextual Q&A with Source Citation
    - Real-time Language Coaching & Feedback
    - Multi-language Translation
    - Personalized Learning Reports
    - Semantic Search with Vector Database

    Built with: FastAPI, PostgreSQL, Chroma DB, Google Gemini API
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration - Restrict to Firebase Hosting domain
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
if ENVIRONMENT == "production":
    ALLOWED_ORIGINS = [
        os.getenv("FRONTEND_URL", "https://your-project.web.app"),
        os.getenv("FRONTEND_URL_FIREBASEAPP", "https://your-project.firebaseapp.com")
    ]
else:
    # Development: Allow all for easier tunneling and local testing
    ALLOWED_ORIGINS = ["*"]  # broadened to avoid tunnel origin mismatch

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Total-Count"]
)


# Request ID Middleware for Tracing
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """
    Add unique request ID for tracing and logging.
    """
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Log request
    logger.info(
        "Incoming request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None
        }
    )

    # Process request
    start_time = datetime.now()
    response = await call_next(request)
    duration = (datetime.now() - start_time).total_seconds()

    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id

    # Log response
    logger.info(
        "Request completed",
        extra={
            "request_id": request_id,
            "status_code": response.status_code,
            "duration_seconds": duration
        }
    )

    return response


# Exception Handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# Health Check Endpoint for Cloud Run
@app.get("/health", tags=["Health"])
async def health_check(request: Request) -> Dict[str, Any]:
    """
    Health check endpoint for Cloud Run and monitoring.

    Returns:
        dict: System health status including:
            - status: "healthy" or "unhealthy"
            - timestamp: Current ISO timestamp
            - environment: Current environment (dev/prod)
            - agents_active: Number of active AI agents
            - services: Status of each service
            - gemini_quota: Remaining Gemini API quota info
    """
    degraded_mode = os.getenv("DEGRADED_MODE", "false").lower() in {"1", "true", "yes"}
    health_status: Dict[str, Any] = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": ENVIRONMENT + (" (degraded)" if degraded_mode else ""),
        "agents_active": 7,
        "services": {}
    }

    try:
        # Check Database
        try:
            if degraded_mode:
                raise RuntimeError("degraded mode")
            from sqlalchemy import text
            db = next(get_db_session())
            db.execute(text("SELECT 1"))
            health_status["services"]["database"] = "healthy"
            db.close()
        except Exception as e:
            logger.warning(f"Database health check skipped/failed: {str(e)}")
            health_status["services"]["database"] = "unavailable"
            health_status["status"] = "degraded"

        # Check Vector Store
        try:
            if getattr(request.app.state, 'vector_store', None):
                health_status["services"]["vector_store"] = "healthy"
            else:
                health_status["services"]["vector_store"] = "not_initialized"
                health_status["status"] = "degraded"
        except Exception as e:
            logger.warning(f"Vector store health check failed: {str(e)}")
            health_status["services"]["vector_store"] = "unhealthy"

        # Check Gemini API
        try:
            if getattr(request.app.state, 'gemini_client', None):
                quota_info = request.app.state.gemini_client.get_quota_status()
                health_status["services"]["gemini_api"] = "healthy"
                health_status["gemini_quota"] = quota_info
            else:
                health_status["services"]["gemini_api"] = "not_initialized"
                health_status["gemini_quota"] = {"available": False}
                health_status["status"] = "degraded"
        except Exception as e:
            logger.warning(f"Gemini API health check failed: {str(e)}")
            health_status["services"]["gemini_api"] = "unhealthy"
            health_status["gemini_quota"] = {"available": False, "error": str(e)}

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Root Endpoint
@app.get("/", tags=["Root"])
async def root() -> Dict[str, Any]:
    """
    Root endpoint with API information.
    """
    return {
        "message": "Multi-Agent PDF Intelligence + Language Learning Platform",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs",
        "health": "/health",
        "api_prefix": "/api",
        "author": "Santosh Yadav",
        "degraded_mode": os.getenv("DEGRADED_MODE", "false").lower() in {"1", "true", "yes"}
    }

# Include API Routes
app.include_router(api_router, prefix="/api", tags=["API"])


# Main entry point
if __name__ == "__main__":
    PORT = int(os.getenv("PORT", 8080))
    HOST = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting server on {HOST}:{PORT}")

    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=ENVIRONMENT == "development",
        log_level="info",
        access_log=True
    )
