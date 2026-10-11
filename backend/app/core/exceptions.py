"""Centralized exception handlers for the application."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


def get_request_id(request: Request) -> str:
    """Get the request ID assigned by middleware."""
    return getattr(request.state, "request_id", "-")


def create_error_response(
    status_code: int,
    code: str,
    message: str,
    request_id: str,
    details: Any = None,
) -> JSONResponse:
    """Create a consistent JSON error response."""

    error: dict[str, Any] = {
        "code": code,
        "message": message,
        "request_id": request_id,
    }

    if details is not None:
        error["details"] = details

    return JSONResponse(
        status_code=status_code,
        content={"error": error},
        headers={"X-Request-ID": request_id},
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Handle expected HTTP errors."""

    message = (
        str(exc.detail)
        if isinstance(exc.detail, str) and exc.status_code < 500
        else "Request failed"
    )

    details = (
        exc.detail
        if not isinstance(exc.detail, str) and exc.status_code < 500
        else None
    )

    return create_error_response(
        status_code=exc.status_code,
        code=f"HTTP_{exc.status_code}",
        message=message,
        request_id=get_request_id(request),
        details=jsonable_encoder(details) if details is not None else None,
    )

async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle invalid request data without exposing raw input."""

    safe_errors = [
        {
            "field": ".".join(str(part) for part in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]

    return create_error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message="Request validation failed",
        request_id=get_request_id(request),
        details=safe_errors,
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected server errors without exposing internals."""

    logger.error(
        "Unhandled application exception",
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    return create_error_response(
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        request_id=get_request_id(request),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register application-wide exception handlers."""

    app.add_exception_handler(
        StarletteHTTPException,
        http_exception_handler,
    )
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )
    app.add_exception_handler(
        Exception,
        unhandled_exception_handler,
    )

