from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.agent.engine import run_agent
from app.log import get_logger

logger = get_logger("routers.agent")
router = APIRouter()


class AgentRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Savolingiz")
    max_tool_rounds: int = Field(default=8, ge=1, le=20)


class AgentResponse(BaseModel):
    answer: str
    tool_calls: int = 0


@router.post("/agent/ask", response_model=AgentResponse)
async def ask_agent(req: AgentRequest) -> AgentResponse:
    answer = await run_agent(req.query, max_tool_rounds=req.max_tool_rounds)
    return AgentResponse(answer=answer)
