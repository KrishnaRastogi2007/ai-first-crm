# Unit tests for application health endpoints.

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

import app.health.router as health_module
from app.main import app

client = TestClient(app)


class FakeConnection:
    """Simulate a database connection."""

    def __init__(self, error=None):
        self.error = error

    async def __aenter__(self):
        if self.error:
            raise self.error
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def execute(self, statement):
        return None


class FakeEngine:
    """Simulate the database engine."""

    def __init__(self, connection_error=None):
        self.connection_error = connection_error

    def connect(self):
        return FakeConnection(self.connection_error)


def test_health_returns_healthy():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_ready_returns_200_when_database_is_available(monkeypatch):
    monkeypatch.setattr(health_module, "engine", FakeEngine())

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "available",
    }


def test_ready_returns_503_when_database_fails(monkeypatch):
    monkeypatch.setattr(
        health_module,
        "engine",
        FakeEngine(
            connection_error=SQLAlchemyError("Database unavailable")
        ),
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "HTTP_503"
    assert response.json()["error"]["message"] == "Request failed"


def test_ready_returns_503_on_timeout(monkeypatch):
    monkeypatch.setattr(
        health_module,
        "engine",
        FakeEngine(connection_error=TimeoutError()),
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "HTTP_503"
    assert response.json()["error"]["message"] == "Request failed"