from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from pydantic import BaseModel

from app.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.agents.orchestrator import OrchestratorAgent

router = APIRouter(prefix="/chat", tags=["chat"])
orchestrator = OrchestratorAgent()

class ChatRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, str]]] = None

class ChatResponse(BaseModel):
    routed_agent: str
    response: str
    detected_state: str
    verses_cited: List[str]

@router.post("", response_model=ChatResponse)
async def chat_with_orchestrator(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = await orchestrator.route_and_resolve(
        user_id=current_user.id,
        query=request.query,
        history=request.history,
        db_session=db
    )
    return ChatResponse(
        routed_agent=result.get("routed_agent", "Orchestrator"),
        response=result.get("response", ""),
        detected_state=result.get("detected_state", "calm"),
        verses_cited=result.get("verses_cited", [])
    )
