from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
import json
import logging

from app.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.journal import JournalEntry
from app.agents.base import BaseAgent

logger = logging.getLogger("garuda_dharma.journal")

router = APIRouter(prefix="/journal", tags=["journal"])

# Analysis agent helper
journal_analyzer = BaseAgent(
    name="Journal Analyzer",
    system_prompt=(
        "You are an emotional and spiritual state classifier. "
        "Analyze the user's journal entry and return a JSON object with: "
        "'sentiment_score' (float between -1.0 and 1.0), "
        "'dominant_emotion' (string from: calm, anxious, distracted, overloaded, sad, happy, peaceful), "
        "and 'reflection_depth' (integer 1-5 where 1 is surface level daily details, 5 is deep spiritual self-inquiry)."
        "Do NOT return any other text, prefix, or suffix. Return valid raw JSON only."
    )
)

class JournalCreate(BaseModel):
    content: str
    prompt_used: Optional[str] = None

class JournalOut(BaseModel):
    id: int
    content: str
    prompt_used: Optional[str]
    sentiment_score: float
    dominant_emotion: str
    reflection_depth: int
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("", response_model=List[JournalOut])
def get_journals(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(JournalEntry).filter(JournalEntry.user_id == current_user.id).order_by(JournalEntry.created_at.desc()).all()

@router.post("", response_model=JournalOut)
async def create_journal_entry(
    entry_in: JournalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Create preliminary db entry
    entry = JournalEntry(
        user_id=current_user.id,
        content=entry_in.content,
        prompt_used=entry_in.prompt_used,
        sentiment_score=0.0,
        dominant_emotion="neutral",
        reflection_depth=1
    )
    
    # Run background analysis via local LLM
    try:
        analysis_raw = await journal_analyzer.generate_response(entry_in.content)
        # Parse JSON from Ollama
        # Remove any Markdown code fences if Ollama adds them
        cleaned_json = analysis_raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned_json)
        
        entry.sentiment_score = float(data.get("sentiment_score", 0.0))
        entry.dominant_emotion = str(data.get("dominant_emotion", "neutral"))
        entry.reflection_depth = int(data.get("reflection_depth", 1))
    except Exception as e:
        logger.error(f"Failed to analyze journal entry: {str(e)}")
        # Default fallback values based on simple text heuristics
        if "stressed" in entry_in.content or "overwhelm" in entry_in.content:
            entry.dominant_emotion = "overloaded"
        elif "happy" in entry_in.content or "peace" in entry_in.content:
            entry.dominant_emotion = "peaceful"
            entry.sentiment_score = 0.5
            
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
