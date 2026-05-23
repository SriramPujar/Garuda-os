import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.workspace import SpiritualNote, NoteLink, DharmicTask
from app.config import settings

logger = logging.getLogger("garuda_dharma.workspace")

router = APIRouter(prefix="/workspace", tags=["workspace"])

# --- Pydantic Schemas ---
class NoteCreate(BaseModel):
    title: str
    content: str
    category: Optional[str] = "Realization"
    tags: Optional[str] = ""

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None

class NoteOut(BaseModel):
    id: int
    title: str
    content: Optional[str]
    category: Optional[str]
    ai_summary: Optional[str]
    tags: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class NoteLinkCreate(BaseModel):
    source_note_id: int
    target_note_id: int
    link_type: Optional[str] = "ref"

class LinkOut(BaseModel):
    id: int
    source_note_id: int
    target_note_id: int
    link_type: str

    class Config:
        from_attributes = True

class TaskCreate(BaseModel):
    title: str
    details: Optional[str] = None
    category: str  # Chanting, Meditation, Scripture, Seva, Fasting, Ritual
    target_date: Optional[date] = None
    due_time: Optional[str] = None
    repeat_frequency: Optional[str] = "none"

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    details: Optional[str] = None
    category: Optional[str] = None
    target_date: Optional[date] = None
    due_time: Optional[str] = None
    is_completed: Optional[bool] = None
    repeat_frequency: Optional[str] = None

class TaskOut(BaseModel):
    id: int
    title: str
    details: Optional[str]
    category: str
    target_date: Optional[date]
    due_time: Optional[str]
    is_completed: bool
    repeat_frequency: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- API Endpoints ---

# Note CRUD
@router.get("/notes", response_model=List[NoteOut])
def get_notes(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(SpiritualNote).filter(SpiritualNote.user_id == current_user.id)
    if category:
        query = query.filter(SpiritualNote.category == category)
    return query.order_by(SpiritualNote.updated_at.desc()).all()

def parse_and_create_bracket_links(note: SpiritualNote, db: Session, user_id: int):
    import re
    if not note.content:
        return
    
    matches = re.findall(r'\[\[(.*?)\]\]', note.content)
    for match in matches:
        title = match.strip()
        if not title:
            continue
        
        target_note = db.query(SpiritualNote).filter(
            SpiritualNote.user_id == user_id,
            SpiritualNote.title.ilike(title)
        ).first()
        
        if target_note and target_note.id != note.id:
            exists = db.query(NoteLink).filter(
                ((NoteLink.source_note_id == note.id) & (NoteLink.target_note_id == target_note.id)) |
                ((NoteLink.source_note_id == target_note.id) & (NoteLink.target_note_id == note.id))
            ).first()
            
            if not exists:
                link = NoteLink(
                    source_note_id=note.id,
                    target_note_id=target_note.id,
                    link_type="ref"
                )
                db.add(link)
    db.commit()

@router.post("/notes", response_model=NoteOut)
async def create_note(
    note_in: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = SpiritualNote(
        user_id=current_user.id,
        title=note_in.title,
        content=note_in.content,
        category=note_in.category,
        tags=note_in.tags,
        ai_summary="Generating reflection summary..."
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    
    # Parse bracket links automatically
    parse_and_create_bracket_links(note, db, current_user.id)
    db.refresh(note)

    
    # Try calling Ollama asynchronously/quickly to summarize and suggest tags
    if note.content and len(note.content) > 50:
        prompt = f"""
        Analyze this spiritual reflection note:
        Title: {note.title}
        Content: {note.content}
        
        Provide a 1-sentence spiritual summary/realization and 3 relevant tags (comma separated).
        Return as JSON:
        {{
          "summary": "1-sentence summary...",
          "tags": "tag1, tag2, tag3"
        }}
        """
        try:
            import sys
            import os
            timeout_val = 1.0 if ("pytest" in sys.modules or os.getenv("TESTING") == "true") else 10.0
            async with httpx.AsyncClient(timeout=timeout_val) as client:
                payload = {
                    "model": settings.OLLAMA_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                }
                response = await client.post(f"{settings.OLLAMA_BASE_URL}/api/chat", json=payload)
                if response.status_code == 200:
                    import json
                    res = response.json()
                    c = res.get("message", {}).get("content", "").strip()
                    if c.startswith("```json"):
                        c = c[7:]
                    if c.endswith("```"):
                        c = c[:-3]
                    parsed = json.loads(c.strip())
                    note.ai_summary = parsed.get("summary", note.ai_summary)
                    if parsed.get("tags"):
                        note.tags = parsed.get("tags")
                    db.commit()
                    db.refresh(note)
        except Exception as e:
            logger.error(f"Error calling Ollama for note summary: {str(e)}")
            note.ai_summary = "Note created. Connect to Ollama for AI reflection insights."
            db.commit()
            db.refresh(note)
            
    return note

# Obsidian Graph Mapping
@router.get("/notes/graph")
def get_notes_graph(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns nodes (notes) and links (connections) for force-directed graph rendering.
    """
    notes = db.query(SpiritualNote).filter(SpiritualNote.user_id == current_user.id).all()
    note_ids = [n.id for n in notes]
    
    # Get links that connect notes belonging to this user
    links = db.query(NoteLink).filter(
        NoteLink.source_note_id.in_(note_ids),
        NoteLink.target_note_id.in_(note_ids)
    ).all()
    
    nodes_data = [
        {
            "id": n.id,
            "title": n.title,
            "category": n.category or "General",
            "tags": n.tags or ""
        }
        for n in notes
    ]
    
    links_data = [
        {
            "id": l.id,
            "source": l.source_note_id,
            "target": l.target_note_id,
            "type": l.link_type
        }
        for l in links
    ]
    
    # Seed default notes if empty so user has something to look at in the graph
    if not nodes_data:
        n1 = SpiritualNote(
            user_id=current_user.id,
            title="Understanding Atman",
            content="The True Self (Atman) is eternal, changeless, and identical to Brahman.",
            category="Vedanta",
            tags="atman, self, philosophy"
        )
        n2 = SpiritualNote(
            user_id=current_user.id,
            title="Nishkama Karma Practice",
            content="Acting without desire for fruits. Key teaching from Bhagavad Gita Ch 2.",
            category="Gita study",
            tags="karma, duty, gita"
        )
        n3 = SpiritualNote(
            user_id=current_user.id,
            title="Sadhana Routine Design",
            content="Establishing morning japam (chanting) and meditation during Brahma Muhurta.",
            category="Realization",
            tags="sadhana, chanting, meditation"
        )
        db.add(n1)
        db.add(n2)
        db.add(n3)
        db.commit()
        db.refresh(n1)
        db.refresh(n2)
        db.refresh(n3)
        
        # Link n1 and n2, n2 and n3
        l1 = NoteLink(source_note_id=n1.id, target_note_id=n2.id, link_type="ref")
        l2 = NoteLink(source_note_id=n2.id, target_note_id=n3.id, link_type="ref")
        db.add(l1)
        db.add(l2)
        db.commit()
        
        nodes_data = [
            {"id": n1.id, "title": n1.title, "category": n1.category, "tags": n1.tags},
            {"id": n2.id, "title": n2.title, "category": n2.category, "tags": n2.tags},
            {"id": n3.id, "title": n3.title, "category": n3.category, "tags": n3.tags}
        ]
        links_data = [
            {"id": l1.id, "source": l1.source_note_id, "target": l1.target_note_id, "type": l1.link_type},
            {"id": l2.id, "source": l2.source_note_id, "target": l2.target_note_id, "type": l2.link_type}
        ]
        
    return {
        "nodes": nodes_data,
        "links": links_data
    }

@router.get("/notes/{note_id}", response_model=NoteOut)
def get_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = db.query(SpiritualNote).filter(
        SpiritualNote.id == note_id,
        SpiritualNote.user_id == current_user.id
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@router.put("/notes/{note_id}", response_model=NoteOut)
def update_note(
    note_id: int,
    note_in: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = db.query(SpiritualNote).filter(
        SpiritualNote.id == note_id,
        SpiritualNote.user_id == current_user.id
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
        
    for field, value in note_in.dict(exclude_unset=True).items():
        setattr(note, field, value)
        
    note.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(note)
    
    # Parse bracket links automatically
    parse_and_create_bracket_links(note, db, current_user.id)
    db.refresh(note)
    
    return note

@router.delete("/notes/{note_id}")
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = db.query(SpiritualNote).filter(
        SpiritualNote.id == note_id,
        SpiritualNote.user_id == current_user.id
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Delete note links referencing this note
    db.query(NoteLink).filter(
        (NoteLink.source_note_id == note_id) | (NoteLink.target_note_id == note_id)
    ).delete()
    
    db.delete(note)
    db.commit()
    return {"status": "success", "message": "Note and its links deleted"}


@router.post("/notes/links", response_model=LinkOut)
def create_note_link(
    link_in: NoteLinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify both notes belong to user
    source = db.query(SpiritualNote).filter(
        SpiritualNote.id == link_in.source_note_id,
        SpiritualNote.user_id == current_user.id
    ).first()
    target = db.query(SpiritualNote).filter(
        SpiritualNote.id == link_in.target_note_id,
        SpiritualNote.user_id == current_user.id
    ).first()
    
    if not source or not target:
        raise HTTPException(status_code=400, detail="Source or Target note not found or access denied")
        
    # Check if link already exists
    exists = db.query(NoteLink).filter(
        NoteLink.source_note_id == link_in.source_note_id,
        NoteLink.target_note_id == link_in.target_note_id
    ).first()
    if exists:
        return exists
        
    link = NoteLink(
        source_note_id=link_in.source_note_id,
        target_note_id=link_in.target_note_id,
        link_type=link_in.link_type
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link

@router.delete("/notes/links/{link_id}")
def delete_note_link(
    link_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    link = db.query(NoteLink).filter(NoteLink.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
        
    # Verify owner
    source = db.query(SpiritualNote).filter(
        SpiritualNote.id == link.source_note_id,
        SpiritualNote.user_id == current_user.id
    ).first()
    if not source:
        raise HTTPException(status_code=403, detail="Forbidden")
        
    db.delete(link)
    db.commit()
    return {"status": "success", "message": "Link deleted"}

# Dharmic Tasks / Sadhana Tracker
@router.get("/tasks", response_model=List[TaskOut])
def get_tasks(
    category: Optional[str] = None,
    is_completed: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(DharmicTask).filter(DharmicTask.user_id == current_user.id)
    if category:
        query = query.filter(DharmicTask.category == category)
    if is_completed is not None:
        query = query.filter(DharmicTask.is_completed == is_completed)
        
    return query.order_by(DharmicTask.target_date.asc(), DharmicTask.id.asc()).all()

@router.post("/tasks", response_model=TaskOut)
def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = DharmicTask(
        user_id=current_user.id,
        title=task_in.title,
        details=task_in.details,
        category=task_in.category,
        target_date=task_in.target_date or date.today(),
        due_time=task_in.due_time or "05:00 AM",
        repeat_frequency=task_in.repeat_frequency or "none",
        is_completed=False
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(DharmicTask).filter(
        DharmicTask.id == task_id,
        DharmicTask.user_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    for field, value in task_in.dict(exclude_unset=True).items():
        setattr(task, field, value)
        
    db.commit()
    db.refresh(task)
    return task

@router.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(DharmicTask).filter(
        DharmicTask.id == task_id,
        DharmicTask.user_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"status": "success", "message": "Task deleted"}
