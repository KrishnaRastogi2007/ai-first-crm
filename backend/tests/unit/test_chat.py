
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.chat import router
from app.core.dependencies import get_current_user


@pytest.fixture
def app():
    test_app = FastAPI()
    test_app.include_router(router)

    test_app.dependency_overrides[get_current_user] = (
        lambda: SimpleNamespace(id=1, role="admin")
    )

    return test_app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_chat_invokes_graph_with_message_and_token(client):
    graph_result = {
        "messages": [
            SimpleNamespace(content="Found Dr. Sharma.")
        ]
    }

    with patch(
        "app.api.v1.chat.hcp_graph.ainvoke",
        new_callable=AsyncMock,
        return_value=graph_result,
    ) as mock_invoke:
        response = client.post(
            "/chat",
            headers={"Authorization": "Bearer test-access-token"},
            json={"message": "Find Dr. Sharma"},
        )

    assert response.status_code == 200
    assert response.json() == {"reply": "Found Dr. Sharma."}

    mock_invoke.assert_awaited_once()
    args, kwargs = mock_invoke.await_args

    assert args[0]["messages"][0].content == "Find Dr. Sharma"
    assert kwargs["config"]["configurable"]["access_token"] == (
        "test-access-token"
    )


def test_chat_rejects_missing_access_token(client):
    response = client.post(
        "/chat",
        json={"message": "Find Dr. Sharma"},
    )

    assert response.status_code == 401


def test_chat_rejects_empty_message(client):
    response = client.post(
        "/chat",
        headers={"Authorization": "Bearer test-access-token"},
        json={"message": "   "},
    )

    assert response.status_code == 422


def test_chat_handles_graph_failure(client):
    with patch(
        "app.api.v1.chat.hcp_graph.ainvoke",
        new_callable=AsyncMock,
        side_effect=RuntimeError("test failure"),
    ):
        response = client.post(
            "/chat",
            headers={"Authorization": "Bearer test-access-token"},
            json={"message": "Find Dr. Sharma"},
        )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "The AI agent could not complete the request."
    )
