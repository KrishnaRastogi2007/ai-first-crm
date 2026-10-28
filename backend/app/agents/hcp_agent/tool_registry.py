"""
Agent ko batata hai available tools kaunse hain.

search_hcp
log_interaction
edit_interaction
interaction_history
follow_up
summarize_interaction

Memory:

Registry = available tools ki list
"""
"""Tool registry for the HCP LangGraph agent."""

from langchain_core.tools import BaseTool

from app.tools.search_hcp import search_hcp
from app.tools.log_interaction import log_interaction
from app.tools.edit_interaction import edit_interaction


HCP_TOOLS: list[BaseTool] = [
    search_hcp,
    log_interaction,
    edit_interaction,
]


def get_hcp_tools() -> list[BaseTool]:
    """Return the tools available to the HCP agent."""
    return HCP_TOOLS.copy()

