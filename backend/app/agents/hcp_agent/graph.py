
"""LangGraph workflow for the HCP agent."""

from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from app.agents.hcp_agent.nodes import call_model
from app.agents.hcp_agent.routing import route_after_model
from app.agents.hcp_agent.tool_registry import get_hcp_tools


def build_hcp_graph():
    """Build and compile the HCP agent graph."""

    tools = get_hcp_tools()

    graph = StateGraph(MessagesState)

    # Node that calls the Groq model.
    graph.add_node("call_model", call_model)

    # Node that executes requested tools.
    graph.add_node("tools", ToolNode(tools))

    # Start by asking the model what to do.
    graph.add_edge(START, "call_model")

    # Route based on whether the model requested a tool.
    graph.add_conditional_edges(
        "call_model",
        route_after_model,
        {
            "tools": "tools",
            END: END,
        },
    )

    # After tool execution, let the model interpret the results.
    graph.add_edge("tools", "call_model")

    return graph.compile()


hcp_graph = build_hcp_graph()
