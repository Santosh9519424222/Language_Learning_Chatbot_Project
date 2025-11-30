"""
Error Handling Middleware
Provides minimal JSON error responses and exception handlers.

Author: Santosh Yadav
Date: November 2025
"""
from typing import Dict, Any
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "detail": exc.errors(),
            "path": request.url.path
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "path": request.url.path
        }
    )


def handle_pdf_error(exc: Exception) -> Dict[str, Any]:
    """Map PDF errors to user-friendly messages."""
    logger.error(f"PDF error: {exc}")
    return {
        "user_message": "Failed to process PDF. Please ensure it's a valid, non-encrypted PDF under 50MB.",
        "error": str(exc)
    }


def handle_gemini_error(exc: Exception) -> Dict[str, Any]:
    """Map Gemini API errors to user-friendly messages."""
    logger.error(f"Gemini API error: {exc}")
    return {
        "user_message": "AI service is temporarily unavailable. Please try again later.",
        "error": str(exc)
    }

