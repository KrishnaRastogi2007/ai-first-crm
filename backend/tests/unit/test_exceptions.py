"""Tests for centralized exception handlers."""

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.api.middleware.request_id import RequestIDMiddleware
from app.core.exceptions import register_exception_handlers
from pydantic import BaseModel


def create_test_app() -> FastAPI:
    """Create an isolated app for exception handler tests."""

    test_app = FastAPI()
    register_exception_handlers(test_app)
    test_app.add_middleware(RequestIDMiddleware)

    @test_app.get("/test-error")
    async def raise_unexpected_error(request: Request) -> None:
        raise RuntimeError("Sensitive internal error details")

    return test_app


def test_unhandled_exception_returns_safe_json() -> None:
    """Unexpected errors should return a safe, standardized response."""

    test_app = create_test_app()

    # Keep the test client running even when the endpoint raises an error.
    with TestClient(test_app, raise_server_exceptions=False) as client:
        response = client.get("/test-error")

    assert response.status_code == 500
    assert response.headers["X-Request-ID"]
    assert response.json() == {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "request_id": response.headers["X-Request-ID"],
        }
    }
    assert "Sensitive internal error details" not in response.text


def test_unknown_route_returns_standard_404() -> None:
    """Unknown routes should return a standardized 404 response."""

    test_app = create_test_app()

    with TestClient(test_app) as client:
        response = client.get("/route-that-does-not-exist")

    assert response.status_code == 404
    assert response.headers["X-Request-ID"]

    body = response.json()
    assert body["error"]["code"] == "HTTP_404"
    assert body["error"]["message"] == "Not Found"
    assert body["error"]["request_id"] == response.headers["X-Request-ID"]


def test_invalid_request_returns_safe_422() -> None:
    """Validation errors should not expose raw input."""

    test_app = create_test_app()

    @test_app.post("/test-validation")
    async def validate_payload(payload: dict[str, str]) -> dict[str, str]:
        return payload

    with TestClient(test_app) as client:
        response = client.post("/test-validation", json={"unexpected": "value"})

    assert response.status_code == 200


class RequiredPayload(BaseModel):
    name: str


def test_invalid_request_returns_safe_422() -> None:
    """Validation errors should not expose raw input."""

    test_app = create_test_app()

    @test_app.post("/test-validation")
    async def validate_payload(payload: RequiredPayload) -> dict[str, str]:
        return {"name": payload.name}

    with TestClient(test_app) as client:
        response = client.post(
            "/test-validation",
            json={"unexpected": "value"},
        )

    assert response.status_code == 422
    assert response.headers["X-Request-ID"]

    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "Request validation failed"
    assert body["error"]["request_id"] == response.headers["X-Request-ID"]

    details = body["error"]["details"]
    assert any(item["field"] == "body.name" for item in details)
    assert "input" not in str(details)


