"""Tests for request ID middleware."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.middleware.request_id import RequestIDMiddleware


def test_request_id_is_returned_in_response_header() -> None:
    """Each HTTP response should include an X-Request-ID header."""

    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/test")
    async def test_endpoint() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") is not None
    assert len(response.headers["X-Request-ID"]) > 0


def test_each_request_gets_a_unique_request_id() -> None:
    """Separate HTTP requests should receive different request IDs."""

    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/test")
    async def test_endpoint() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(app)

    first_response = client.get("/test")
    second_response = client.get("/test")

    first_request_id = first_response.headers["X-Request-ID"]
    second_request_id = second_response.headers["X-Request-ID"]

    assert first_request_id != second_request_id