
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool

from app.agents.hcp_agent.graph import build_hcp_graph


@pytest.mark.asyncio
async def test_graph_executes_search_tool_and_returns_final_answer():
    # Step 1: Simulate the model requesting an HCP search.
    tool_call_message = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "fake_search_hcp",
                "args": {
                    "email": "amit.sharma@example.com",
                    "email_exact": True,
                },
                "id": "search-call-1",
                "type": "tool_call",
            }
        ],
    )

    # Step 2: Simulate the model's final answer.
    final_message = AIMessage(
        content="Found the HCP with the requested email."
    )

    # Step 3: Mock the model and its async responses.
    mock_model = MagicMock()
    mock_model.bind_tools.return_value = mock_model
    mock_model.ainvoke = AsyncMock(
        side_effect=[tool_call_message, final_message]
    )

    # Step 4: Mock the result returned by the search tool.
    mock_tool = AsyncMock(
        return_value={
            "success": True,
            "data": {
                "items": [
                    {
                        "name": "Dr. Amit Sharma",
                        "email": "amit.sharma@example.com",
                    }
                ],
                "total": 1,
            },
        }
    )

    # Step 5: Create a real LangChain tool around the mock.
    @tool
    async def fake_search_hcp(
        email: str,
        email_exact: bool = False,
    ) -> dict:
        """Search HCP records by email."""
        return await mock_tool(
            email=email,
            email_exact=email_exact,
        )

    # Step 6: Replace model/tool dependencies only during this test.
    with (
        patch(
            "app.agents.hcp_agent.nodes.groq_client.get_chat_model",
            return_value=mock_model,
        ),
        patch(
            "app.agents.hcp_agent.nodes.get_hcp_tools",
            return_value=[fake_search_hcp],
        ),
        patch(
            "app.agents.hcp_agent.graph.get_hcp_tools",
            return_value=[fake_search_hcp],
        ),
    ):
        graph = build_hcp_graph()

        result = await graph.ainvoke(
            {
                "messages": [
                    HumanMessage(
                        content=(
                            "Find the HCP with email "
                            "amit.sharma@example.com"
                        )
                    )
                ]
            },
            config={
                "configurable": {
                    "access_token": "test-access-token",
                }
            },
        )

    # Step 7: Verify the tool was called with the expected filters.
    mock_tool.assert_awaited_once_with(
        email="amit.sharma@example.com",
        email_exact=True,
    )

    # Verify the model was called twice:
    # first to request the tool, then to generate the final answer.
    assert mock_model.ainvoke.await_count == 2

    # Verify the graph returns the final model response.
    assert result["messages"][-1].content == (
        "Found the HCP with the requested email."
    )
