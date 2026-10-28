"""
User:

"Change the sentiment from neutral to positive."

Agent:

edit_interaction

Existing interaction find karega aur update karega.

"""

"""Tool for updating an existing CRM interaction."""

import logging
from typing import Any

import httpx
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.core.config import settings

logger = logging.getLogger(__name__)


@tool
async def edit_interaction(
    config: RunnableConfig,
    interaction_id: int,
    interaction_type: str | None = None,
    subject: str | None = None,
    notes: str | None = None,
    interaction_date: str | None = None,
) -> dict[str, Any]:
    """Update an existing interaction.

    Use when the user asks to edit a previously recorded meeting,
    call, email, or other interaction. Only change fields supplied
    by the user; preserve all other existing fields.
    """

    if interaction_id < 1:
        return {
            "success": False,
            "error": "Interaction ID must be a positive integer.",
        }

    access_token = config.get("configurable", {}).get("access_token")

    if not access_token:
        return {
            "success": False,
            "error": "Authentication context is missing. Please log in first.",
        }

    base_url = str(settings.API_BASE_URL).rstrip("/")
    url = f"{base_url}/api/v1/interactions/{interaction_id}"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=3.0),
            follow_redirects=False,
        ) as client:
            # Fetch the existing record so unchanged fields are preserved.
            response = await client.get(url, headers=headers)

            if response.status_code in (401, 403):
                return {
                    "success": False,
                    "error": "You are not authorized to access this interaction.",
                }

            if response.status_code == 404:
                return {
                    "success": False,
                    "error": "Interaction not found.",
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
                    "error": f"Could not retrieve interaction (HTTP {response.status_code}).",
                }

            try:
                existing = response.json()
            except ValueError:
                return {
                    "success": False,
                    "error": "The CRM API returned an invalid response.",
                }

            # Keep existing values unless the user explicitly changes them.
            payload = {
                "hcp_id": existing["hcp_id"],
                "interaction_type": (
                    interaction_type
                    if interaction_type is not None
                    else existing["interaction_type"]
                ),
                "subject": (
                    subject if subject is not None else existing["subject"]
                ),
                "notes": notes if notes is not None else existing.get("notes"),
                "interaction_date": (
                    interaction_date
                    if interaction_date is not None
                    else existing.get("interaction_date")
                ),
            }

            response = await client.put(
                url,
                json=payload,
                headers=headers,
            )

        if response.status_code in (401, 403):
            return {
                "success": False,
                "error": "You are not authorized to update this interaction.",
            }

        if response.status_code == 404:
            return {
                "success": False,
                "error": "Interaction not found.",
            }

        if response.status_code == 422:
            return {
                "success": False,
                "error": "The updated interaction data was rejected by the API.",
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
                "error": f"Interaction update failed (HTTP {response.status_code}).",
            }

        try:
            updated = response.json()
        except ValueError:
            return {
                "success": False,
                "error": "The CRM API returned an invalid response.",
            }

        return {"success": True, "data": updated}

    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "The interaction request timed out.",
        }
    except httpx.RequestError:
        logger.warning("CRM interaction update request failed")
        return {
            "success": False,
            "error": "Could not connect to the CRM API.",
        }
    except (KeyError, TypeError):
        return {
            "success": False,
            "error": "The existing interaction response has an unexpected format.",
        }
