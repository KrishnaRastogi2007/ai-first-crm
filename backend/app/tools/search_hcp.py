
"""
User:
"Find Dr. Sharma."

Agent:
search_hcp

Database se HCP search.
"""

from typing import Annotated, Any
from urllib.parse import urlsplit

import httpx
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from pydantic import Field

from app.core.config import settings


@tool
async def search_hcp(
    config: RunnableConfig,
    hcp_id: Annotated[int | None, Field(ge=1)] = None,
    name: Annotated[str | None, Field(min_length=1, max_length=100)] = None,
    specialty: Annotated[str | None, Field(min_length=1, max_length=150)] = None,
    email: Annotated[str | None, Field(min_length=1, max_length=254)] = None,
    organization: Annotated[str | None, Field(min_length=1, max_length=200)] = None,
    email_exact: bool = False,
    organization_exact: bool = False,
    keyword: Annotated[str | None, Field(min_length=1, max_length=100)] = None,
    page: Annotated[int, Field(ge=1)] = 1,
    limit: Annotated[int, Field(ge=1, le=50)] = 20,
) -> dict[str, Any]:
    """Search HCP records or retrieve one HCP by ID.

    Use hcp_id to retrieve a specific HCP.
    Otherwise, search by name, specialty, email, organization, or keyword.

    Email and organization support partial matching by default.
    Set email_exact or organization_exact to true for exact matching.
    Keyword searches name, specialty, organization, and email.
    Results are paginated.

    The authenticated user's access token is supplied by the
    application through LangGraph runtime configuration.
    """

    # 1. Get the authenticated user's access token.
    configurable = config.get("configurable", {})
    access_token = configurable.get("access_token")

    if not isinstance(access_token, str) or not access_token.strip():
        return {
            "error": "Authentication context is missing. Please authenticate first."
        }

    # 2. Validate the configured API URL.
    base_url = settings.API_BASE_URL.strip().rstrip("/")
    app_env = settings.APP_ENV.lower()

    if not base_url:
        return {"error": "HCP API is not configured."}

    parsed_url = urlsplit(base_url)

    if (
        parsed_url.scheme not in {"http", "https"}
        or not parsed_url.netloc
        or parsed_url.username is not None
        or parsed_url.password is not None
        or parsed_url.query
        or parsed_url.fragment
    ):
        return {"error": "HCP API configuration is invalid."}

    if app_env == "production" and parsed_url.scheme != "https":
        return {"error": "HTTPS is required for the HCP API in production."}

    # 3. Choose ID lookup or filtered search.
    if hcp_id is not None:
        url = f"{base_url}/api/v1/hcps/{hcp_id}"
        params = None
    else:
        url = f"{base_url}/api/v1/hcps"

        params: dict[str, str | int | bool] = {
            "page": page,
            "limit": limit,
        }

        if name is not None and name.strip():
            params["name"] = name.strip()

        if specialty is not None and specialty.strip():
            params["specialty"] = specialty.strip()

        if email is not None and email.strip():
            params["email"] = email.strip()
            params["email_exact"] = email_exact

        if organization is not None and organization.strip():
            params["organization"] = organization.strip()
            params["organization_exact"] = organization_exact

        if keyword is not None and keyword.strip():
            params["keyword"] = keyword.strip()

    # 4. Forward the user's token to the API.
    headers = {
        "Authorization": f"Bearer {access_token.strip()}",
        "Accept": "application/json",
    }

    # 5. Send request with a finite timeout.
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=3.0),
            follow_redirects=False,
        ) as client:
            response = await client.get(
                url,
                params=params,
                headers=headers,
            )

        # 6. Handle API errors safely.
        if response.status_code == 401:
            return {
                "error": "Authentication failed. Please sign in again."
            }

        if response.status_code == 403:
            return {
                "error": "You are not authorized to access these HCP records."
            }

        if response.status_code == 404:
            return {
                "error": (
                    f"HCP with ID {hcp_id} was not found."
                    if hcp_id is not None
                    else "The requested resource was not found."
                )
            }

        if response.status_code == 422:
            return {
                "error": "The HCP API rejected the request parameters."
            }

        if response.status_code == 429:
            return {
                "error": "Too many requests. Please try again later."
            }

        if response.status_code >= 500:
            return {
                "error": "The HCP API is temporarily unavailable."
            }

        response.raise_for_status()

        try:
            data = response.json()
        except ValueError:
            return {
                "error": "The HCP API returned an invalid response."
            }

        return {
            "success": True,
            "data": data,
        }

    except httpx.TimeoutException:
        return {"error": "The HCP API request timed out."}

    except httpx.RequestError:
        return {
            "error": (
                "Could not connect to the HCP API. "
                "Check its configuration and availability."
            )
        }

    except httpx.HTTPStatusError:
        return {"error": "The HCP API request failed."}
