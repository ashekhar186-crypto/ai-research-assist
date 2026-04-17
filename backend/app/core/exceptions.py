"""
app/core/exceptions.py
──────────────────────
Custom exception classes and FastAPI exception handlers.
These give consistent JSON error responses across the API.
"""

from fastapi import Request
from fastapi.responses import JSONResponse


# ── Custom Exception Classes ──────────────────────────────────────────────────

class AppException(Exception):
    """Base exception for all application errors."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundException(AppException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} not found.", status_code=404)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Not authenticated."):
        super().__init__(message, status_code=401)


class ForbiddenException(AppException):
    def __init__(self, message: str = "Access denied."):
        super().__init__(message, status_code=403)


class ValidationException(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=422)


class AgentException(AppException):
    """Raised when the AI agent encounters an unrecoverable error."""
    def __init__(self, message: str):
        super().__init__(f"Agent error: {message}", status_code=500)


class DocumentProcessingException(AppException):
    """Raised when PDF/DOCX processing fails."""
    def __init__(self, message: str):
        super().__init__(f"Document processing failed: {message}", status_code=422)


# ── FastAPI Exception Handlers ────────────────────────────────────────────────

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "message": exc.message, "status_code": exc.status_code}
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": True, "message": "An unexpected server error occurred.", "status_code": 500}
    )