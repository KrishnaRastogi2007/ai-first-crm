
"""LangGraph nodes for the HCP agent."""

import logging
from typing import Any

from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import MessagesState

from app.agents.hcp_agent.tool_registry import get_hcp_tools
from app.integrations.llm import groq_client

logger = logging.getLogger(__name__)


HCP_SYSTEM_PROMPT = """
You are an assistant for a Healthcare Professional (HCP) CRM.

Use the search_hcp tool when the user asks to find HCP records
or retrieve an HCP by ID.

Use the log_interaction tool when the user asks to record a
meeting, call, email, or other interaction with an HCP.

Never invent HCP records or claim an action succeeded unless
the relevant tool confirms the result.

Explain search results and action outcomes clearly and concisely.
"""


async def call_model(
    state: MessagesState,
    config: RunnableConfig,
) -> dict[str, Any]:
    """Call Groq with the conversation and registered HCP tools."""

    tools = get_hcp_tools()
    model = groq_client.get_chat_model().bind_tools(tools)

    messages = [
        SystemMessage(content=HCP_SYSTEM_PROMPT),
        *state["messages"],
    ]

    response = await model.ainvoke(
        messages,
        config=config,
    )

    # Log token usage for this individual model call.
    usage = getattr(response, "usage_metadata", None)

    if usage:
        logger.info(
            "LLM token usage | input=%s output=%s total=%s",
            usage.get("input_tokens"),
            usage.get("output_tokens"),
            usage.get("total_tokens"),
        )
    else:
        logger.info("LLM token usage metadata unavailable")

    return {"messages": [response]}
