
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from app.agents.hcp_agent.graph import hcp_graph
from app.core.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
async def chat(
    data: ChatRequest,
    access_token: str = Depends(oauth2_scheme),
    current_user=Depends(get_current_user),
):
    message = data.message.strip()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Message cannot be empty.",
        )

    try:
        result = await hcp_graph.ainvoke(
            {"messages": [HumanMessage(content=message)]},
            config={
                "configurable": {
                    "access_token": access_token,
                }
            },
        )
    except Exception:
        logger.exception("HCP chat agent execution failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI agent could not complete the request.",
        ) from None

    messages = result.get("messages", [])

    if not messages:
        logger.error("HCP chat agent returned no messages")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI agent returned no response.",
        )

    reply = messages[-1].content

    if not isinstance(reply, str):
        logger.error("HCP chat agent returned an unsupported response type")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI agent returned an unsupported response.",
        )

    return ChatResponse(reply=reply)
