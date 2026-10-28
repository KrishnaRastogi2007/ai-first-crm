"""
AI:

"I met Dr. Sharma today and discussed Product X."

Agent tool:

log_interaction

Structured data bana sakta hai:

{
  "hcp": "Dr. Sharma",
  "type": "Meeting",
  "product": "Product X",
  "sentiment": "Positive",
  "topics": ["Product X"],
  "summary": "Discussed Product X with HCP."
}

Then database mein save

"""


from datetime import datetime
from typing import Any

import httpx
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.core.config import settings


@tool
async def log_interaction(
    config: RunnableConfig,
    hcp_id: int,
    interaction_type: str,
    subject: str,
    notes: str | None = None,
    interaction_date: datetime | None = None,
) -> dict[str, Any]:
    """Create an interaction record for a healthcare professional.

    Use when the user asks to log a meeting, call, email, or other
    interaction with an HCP.
    """
    access_token = config.get("configurable", {}).get("access_token")

    if not access_token:
        return {
            "success": False,
            "error": "Authentication context is missing. Please log in first.",
        }

    payload: dict[str, Any] = {
        "hcp_id": hcp_id,
        "interaction_type": interaction_type,
        "subject": subject,
        "notes": notes,
    }

    if interaction_date is not None:
        payload["interaction_date"] = interaction_date.isoformat()

    url = f"{str(settings.API_BASE_URL).rstrip('/')}/api/v1/interactions"

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=3.0),
            follow_redirects=False,
        ) as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {access_token}"},
            )

        if response.status_code in (401, 403):
            return {
                "success": False,
                "error": "You are not authorized to create this interaction.",
            }

        if response.status_code == 404:
            return {
                "success": False,
                "error": "The requested resource was not found.",
            }

        if response.status_code == 422:
            return {
                "success": False,
                "error": "The interaction data was rejected by the API.",
            }

        if response.status_code == 429:
            return {
                "success": False,
                "error": "Too many requests. Please try again later.",
            }

        if response.status_code >= 500:
            return {
                "success": False,
                "error": "The CRM API is temporarily unavailable.",
            }

        if not response.is_success:
            return {
                "success": False,
                "error": f"Interaction creation failed (HTTP {response.status_code}).",
            }

        try:
            data = response.json()
        except ValueError:
            return {
                "success": False,
                "error": "The CRM API returned an invalid response.",
            }

        return {"success": True, "data": data}

    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "The interaction request timed out.",
        }
    except httpx.RequestError:
        return {
            "success": False,
            "error": "Could not connect to the CRM API.",
        }

