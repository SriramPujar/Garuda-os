from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
import json

from app.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.ritual import RitualTemplate, UserRitualLog

router = APIRouter(prefix="/rituals", tags=["rituals"])

class RitualTemplateOut(BaseModel):
    id: int
    name: str
    deity: str
    description: Optional[str]
    steps_json: str
    offerings_json: Optional[str]
    estimated_duration: int

    class Config:
        from_attributes = True

class RitualLogCreate(BaseModel):
    ritual_name: str
    duration_spent: int
    notes: Optional[str] = None

class RitualLogOut(BaseModel):
    id: int
    ritual_name: str
    completed_at: datetime
    notes: Optional[str]
    duration_spent: int

    class Config:
        from_attributes = True

@router.get("/templates", response_model=List[RitualTemplateOut])
def get_ritual_templates(db: Session = Depends(get_db)):
    templates = db.query(RitualTemplate).all()
    # Populate default templates if empty
    if not templates:
        seed_ritual_templates(db)
        templates = db.query(RitualTemplate).all()
    return templates

@router.get("/templates/{name}", response_model=RitualTemplateOut)
def get_ritual_template_by_name(name: str, db: Session = Depends(get_db)):
    template = db.query(RitualTemplate).filter(RitualTemplate.name.ilike(name)).first()
    if not template:
        raise HTTPException(status_code=404, detail="Ritual template not found")
    return template

@router.post("/logs", response_model=RitualLogOut)
def log_user_ritual(
    log_in: RitualLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    log = UserRitualLog(
        user_id=current_user.id,
        ritual_name=log_in.ritual_name,
        duration_spent=log_in.duration_spent,
        notes=log_in.notes
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def seed_ritual_templates(db: Session):
    templates = [
        RitualTemplate(
            name="Ganesha Panchopachara Puja",
            deity="Ganesha",
            description="A simple 5-step daily ritual dedicated to Lord Ganesha, the remover of obstacles.",
            steps_json=json.dumps([
                {"step_number": 1, "name": "Gandha (Sandalwood Paste)", "instruction": "Apply pure sandalwood paste or vermilion onto the image/deity of Sri Ganesha.", "mantra": "Om Gam Ganapataye Namah Gandham Samarpayami"},
                {"step_number": 2, "name": "Pushpa (Flowers)", "instruction": "Offer fresh red flowers or durva grass at the feet of Lord Ganesha.", "mantra": "Om Gam Ganapataye Namah Pushpam Samarpayami"},
                {"step_number": 3, "name": "Dhupa (Incense)", "instruction": "Wave light incense sticks in front of the deity in clockwise circles.", "mantra": "Om Gam Ganapataye Namah Dhupam Samarpayami"},
                {"step_number": 4, "name": "Deepa (Lamp)", "instruction": "Wave a ghee lamp or sesame oil lamp gently in clockwise motions.", "mantra": "Om Gam Ganapataye Namah Deepam Samarpayami"},
                {"step_number": 5, "name": "Naivedya (Food Offering)", "instruction": "Offer sweet modak, jaggery, or fresh seasonal fruits.", "mantra": "Om Gam Ganapataye Namah Naivedyam Samarpayami"}
            ]),
            offerings_json=json.dumps(["sandalwood paste", "red flowers / durva grass", "incense", "lamp/ghee", "fruits/modak"]),
            estimated_duration=10
        ),
        RitualTemplate(
            name="Shiva Panchakshara Puja",
            deity="Shiva",
            description="A simple meditative worship of Lord Shiva chanting the holy Panchakshara mantra.",
            steps_json=json.dumps([
                {"step_number": 1, "name": "Abhisheka (Bathing)", "instruction": "Offer holy water or milk drops onto the Shiva Lingam.", "mantra": "Om Namah Shivaya Snanam Samarpayami"},
                {"step_number": 2, "name": "Bilva Patra", "instruction": "Offer three-lobed Bilva leaves or fresh flowers at the altar.", "mantra": "Om Namah Shivaya Bilvapatram Samarpayami"},
                {"step_number": 3, "name": "Dhupa & Deepa", "instruction": "Offer light incense and ghee lamp waving slowly.", "mantra": "Om Namah Shivaya Dhupam Deepam Darsayami"},
                {"step_number": 4, "name": "Naivedya", "instruction": "Offer fresh fruits, honey, or raw coconut.", "mantra": "Om Namah Shivaya Naivedyam Samarpayami"},
                {"step_number": 5, "name": "Prarthana & Meditation", "instruction": "Sit quietly in cross-legged posture for 5 minutes chanting Om Namah Shivaya.", "mantra": "Om Namah Shivaya"}
            ]),
            offerings_json=json.dumps(["water/milk", "bilva leaves / white flowers", "incense", "lamp", "coconuts/fruits"]),
            estimated_duration=15
        )
    ]
    for temp in templates:
        db.add(temp)
    db.commit()
