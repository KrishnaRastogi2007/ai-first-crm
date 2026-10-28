
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.tools.search_hcp import search_hcp


@pytest.fixture
def tool_config():
    return {
        "configurable": {
            "access_token": "test-access-token",
        }
    }


@pytest.fixture
def mock_settings():
    with (
        patch("app.tools.search_hcp.settings.API_BASE_URL", "http://testserver"),
        patch("app.tools.search_hcp.settings.APP_ENV", "testing"),
    ):
        yield


@pytest.mark.asyncio
async def test_search_hcp_passes_email_filter(
    tool_config,
    mock_settings,
):
    mock_response = httpx.Response(
        200,
        json={"items": [], "page": 1, "limit": 20, "total": 0, "pages": 0},
        request=httpx.Request("GET", "http://testserver/api/v1/hcps"),
    )

    with patch(
        "app.tools.search_hcp.httpx.AsyncClient",
    ) as mock_client_class:
        mock_client = mock_client_class.return_value.__aenter__.return_value
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await search_hcp.ainvoke(
            {
                "email": "amit.sharma@example.com",
                "email_exact": True,
            },
            config=tool_config,
        )

    assert result["success"] is True

    params = mock_client.get.await_args.kwargs["params"]
    assert params["email"] == "amit.sharma@example.com"
    assert params["email_exact"] is True

    headers = mock_client.get.await_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer test-access-token"


@pytest.mark.asyncio
async def test_search_hcp_passes_organization_filter(
    tool_config,
    mock_settings,
):
    mock_response = httpx.Response(
        200,
        json={"items": [], "page": 1, "limit": 20, "total": 0, "pages": 0},
        request=httpx.Request("GET", "http://testserver/api/v1/hcps"),
    )

    with patch(
        "app.tools.search_hcp.httpx.AsyncClient",
    ) as mock_client_class:
        mock_client = mock_client_class.return_value.__aenter__.return_value
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await search_hcp.ainvoke(
            {
                "organization": "City Heart Clinic",
                "organization_exact": True,
            },
            config=tool_config,
        )

    assert result["success"] is True

    params = mock_client.get.await_args.kwargs["params"]
    assert params["organization"] == "City Heart Clinic"
    assert params["organization_exact"] is True


@pytest.mark.asyncio
async def test_search_hcp_passes_partial_filters(
    tool_config,
    mock_settings,
):
    mock_response = httpx.Response(
        200,
        json={"items": [], "page": 2, "limit": 10, "total": 0, "pages": 0},
        request=httpx.Request("GET", "http://testserver/api/v1/hcps"),
    )

    with patch(
        "app.tools.search_hcp.httpx.AsyncClient",
    ) as mock_client_class:
        mock_client = mock_client_class.return_value.__aenter__.return_value
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await search_hcp.ainvoke(
            {
                "email": "amit.sharma",
                "organization": "Heart Clinic",
                "page": 2,
                "limit": 10,
            },
            config=tool_config,
        )

    assert result["success"] is True

    params = mock_client.get.await_args.kwargs["params"]
    assert params["email"] == "amit.sharma"
    assert params["email_exact"] is False
    assert params["organization"] == "Heart Clinic"
    assert params["organization_exact"] is False
    assert params["page"] == 2
    assert params["limit"] == 10




@pytest.mark.asyncio
async def test_search_hcp_handles_unauthorized(
    tool_config,
    mock_settings,
):
    mock_response = httpx.Response(
        401,
        json={"detail": "Invalid or expired token"},
        request=httpx.Request(
            "GET",
            "http://testserver/api/v1/hcps",
        ),
    )

    with patch(
        "app.tools.search_hcp.httpx.AsyncClient",
    ) as mock_client_class:
        mock_client = (
            mock_client_class.return_value.__aenter__.return_value
        )
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await search_hcp.ainvoke(
            {"email": "amit.sharma@example.com"},
            config=tool_config,
        )

    assert result == {
        "error": "Authentication failed. Please sign in again."
    }



@pytest.mark.asyncio
async def test_search_hcp_handles_forbidden(
    tool_config,
    mock_settings,
):
    mock_response = httpx.Response(
        403,
        json={"detail": "Permission denied"},
        request=httpx.Request(
            "GET",
            "http://testserver/api/v1/hcps",
        ),
    )

    with patch(
        "app.tools.search_hcp.httpx.AsyncClient",
    ) as mock_client_class:
        mock_client = (
            mock_client_class.return_value.__aenter__.return_value
        )
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await search_hcp.ainvoke(
            {"email": "amit.sharma@example.com"},
            config=tool_config,
        )

    assert result == {
        "error": "You are not authorized to access these HCP records."
    }



@pytest.mark.asyncio
async def test_search_hcp_handles_rate_limit(
    tool_config,
    mock_settings,
):
    mock_response = httpx.Response(
        429,
        json={"detail": "Rate limit exceeded"},
        request=httpx.Request(
            "GET",
            "http://testserver/api/v1/hcps",
        ),
    )

    with patch(
        "app.tools.search_hcp.httpx.AsyncClient",
    ) as mock_client_class:
        mock_client = (
            mock_client_class.return_value.__aenter__.return_value
        )
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await search_hcp.ainvoke(
            {"email": "amit.sharma@example.com"},
            config=tool_config,
        )

    assert result == {
        "error": "Too many requests. Please try again later."
    }


@pytest.mark.asyncio
async def test_search_hcp_handles_server_error(
    tool_config,
    mock_settings,
):
    mock_response = httpx.Response(
        500,
        json={"detail": "Internal server error"},
        request=httpx.Request(
            "GET",
            "http://testserver/api/v1/hcps",
        ),
    )

    with patch(
        "app.tools.search_hcp.httpx.AsyncClient",
    ) as mock_client_class:
        mock_client = (
            mock_client_class.return_value.__aenter__.return_value
        )
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await search_hcp.ainvoke(
            {"email": "amit.sharma@example.com"},
            config=tool_config,
        )

    assert result == {
        "error": "The HCP API is temporarily unavailable."
    }


@pytest.mark.asyncio
async def test_search_hcp_handles_timeout(
    tool_config,
    mock_settings,
):
    with patch(
        "app.tools.search_hcp.httpx.AsyncClient",
    ) as mock_client_class:
        mock_client = (
            mock_client_class.return_value.__aenter__.return_value
        )
        mock_client.get = AsyncMock(
            side_effect=httpx.TimeoutException(
                "Request timed out"
            )
        )

        result = await search_hcp.ainvoke(
            {"email": "amit.sharma@example.com"},
            config=tool_config,
        )

    assert result == {
        "error": "The HCP API request timed out."
    }


@pytest.mark.asyncio
async def test_search_hcp_handles_connection_error(
    tool_config,
    mock_settings,
):
    with patch(
        "app.tools.search_hcp.httpx.AsyncClient",
    ) as mock_client_class:
        mock_client = (
            mock_client_class.return_value.__aenter__.return_value
        )
        mock_client.get = AsyncMock(
            side_effect=httpx.ConnectError(
                "Connection refused"
            )
        )

        result = await search_hcp.ainvoke(
            {"email": "amit.sharma@example.com"},
            config=tool_config,
        )

    assert result == {
        "error": (
            "Could not connect to the HCP API. "
            "Check its configuration and availability."
        )
    }


@pytest.mark.asyncio
async def test_search_hcp_handles_not_found(
    tool_config,
    mock_settings,
):
    mock_response = httpx.Response(
        404,
        json={"detail": "Not found"},
        request=httpx.Request(
            "GET",
            "http://testserver/api/v1/hcps",
        ),
    )

    with patch(
        "app.tools.search_hcp.httpx.AsyncClient",
    ) as mock_client_class:
        mock_client = (
            mock_client_class.return_value.__aenter__.return_value
        )
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await search_hcp.ainvoke(
            {"email": "missing@example.com"},
            config=tool_config,
        )

    assert result == {
        "error": "The requested resource was not found."
    }


@pytest.mark.asyncio
async def test_search_hcp_handles_validation_error(
    tool_config,
    mock_settings,
):
    mock_response = httpx.Response(
        422,
        json={"detail": "Invalid parameters"},
        request=httpx.Request(
            "GET",
            "http://testserver/api/v1/hcps",
        ),
    )

    with patch(
        "app.tools.search_hcp.httpx.AsyncClient",
    ) as mock_client_class:
        mock_client = (
            mock_client_class.return_value.__aenter__.return_value
        )
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await search_hcp.ainvoke(
            {"email": "amit.sharma@example.com"},
            config=tool_config,
        )

    assert result == {
        "error": "The HCP API rejected the request parameters."
    }


@pytest.mark.asyncio
async def test_search_hcp_handles_invalid_json(
    tool_config,
    mock_settings,
):
    mock_response = httpx.Response(
        200,
        content=b"not-valid-json",
        headers={"Content-Type": "application/json"},
        request=httpx.Request(
            "GET",
            "http://testserver/api/v1/hcps",
        ),
    )

    with patch(
        "app.tools.search_hcp.httpx.AsyncClient",
    ) as mock_client_class:
        mock_client = (
            mock_client_class.return_value.__aenter__.return_value
        )
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await search_hcp.ainvoke(
            {"email": "amit.sharma@example.com"},
            config=tool_config,
        )

    assert result == {
        "error": "The HCP API returned an invalid response."
    }


@pytest.mark.asyncio
async def test_search_hcp_handles_missing_access_token(
    mock_settings,
):
    result = await search_hcp.ainvoke(
        {"email": "amit.sharma@example.com"},
        config={"configurable": {}},
    )

    assert result == {
        "error": (
            "Authentication context is missing. "
            "Please authenticate first."
        )
    }
