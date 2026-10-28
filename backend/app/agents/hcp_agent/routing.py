"""

Decide karta hai:

Ab next node kaunsa?

Memory:

Routing = direction"""


"""Conditional routing for the HCP LangGraph agent."""

from typing import Literal

from langgraph.graph import END, MessagesState


def route_after_model(
    state: MessagesState,
) -> Literal["tools", "__end__"]:
    """Route to tools when the model requests a tool call."""

    last_message = state["messages"][-1]

    if getattr(last_message, "tool_calls", None):
        return "tools"

    return END
