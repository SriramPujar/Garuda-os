from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.sadhana import SadhanaRoutine, SadhanaLog, SadhanaStreak

router = APIRouter(prefix="/sadhana", tags=["sadhana"])

class RoutineCreate(BaseModel):
    name: str
    description: Optional[str] = None
    routine_type: str # japa, meditation, scripture, pranayama, puja
    target_value: int
    unit: str # counts, minutes, chapters

class RoutineOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    routine_type: str
    target_value: int
    unit: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class LogCreate(BaseModel):
    routine_id: int
    value_completed: int
    notes: Optional[str] = None
    status: Optional[str] = "completed"

class LogOut(BaseModel):
    id: int
    routine_id: int
    completed_at: datetime
    value_completed: int
    notes: Optional[str]
    status: str

    class Config:
        from_attributes = True

class StreakOut(BaseModel):
    current_streak: int
    max_streak: int
    last_completed_date: Optional[date]

@router.get("/routines", response_model=List[RoutineOut])
def get_routines(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(SadhanaRoutine).filter(SadhanaRoutine.user_id == current_user.id).all()

@router.post("/routines", response_model=RoutineOut)
def create_routine(
    routine_in: RoutineCreate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    routine = SadhanaRoutine(
        user_id=current_user.id,
        name=routine_in.name,
        description=routine_in.description,
        routine_type=routine_in.routine_type,
        target_value=routine_in.target_value,
        unit=routine_in.unit
    )
    db.add(routine)
    db.commit()
    db.refresh(routine)
    return routine

@router.post("/logs", response_model=LogOut)
def log_sadhana(
    log_in: LogCreate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # Verify routine belongs to user
    routine = db.query(SadhanaRoutine).filter(
        SadhanaRoutine.id == log_in.routine_id,
        SadhanaRoutine.user_id == current_user.id
    ).first()
    if not routine:
        raise HTTPException(status_code=404, detail="Sadhana routine not found")
        
    log = SadhanaLog(
        routine_id=log_in.routine_id,
        value_completed=log_in.value_completed,
        notes=log_in.notes,
        status=log_in.status
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    
    # Update user streak
    update_streak(current_user.id, db)
    
    return log

@router.get("/streak", response_model=StreakOut)
def get_streak(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    streak = db.query(SadhanaStreak).filter(SadhanaStreak.user_id == current_user.id).first()
    if not streak:
        streak = SadhanaStreak(user_id=current_user.id, current_streak=0, max_streak=0)
        db.add(streak)
        db.commit()
        db.refresh(streak)
    return streak

def update_streak(user_id: int, db: Session):
    today = date.today()
    streak = db.query(SadhanaStreak).filter(SadhanaStreak.user_id == user_id).first()
    if not streak:
        streak = SadhanaStreak(user_id=user_id, current_streak=0, max_streak=0)
        db.add(streak)
        
    last_date = streak.last_completed_date
    if last_date == today:
        # Already logged today, streak remains same
        return
        
    if last_date is None:
        streak.current_streak = 1
    else:
        delta = (today - last_date).days
        if delta == 1:
            streak.current_streak += 1
        elif delta > 1:
            # Streak broken
            streak.current_streak = 1
            
    if streak.current_streak > streak.max_streak:
        streak.max_streak = streak.current_streak
        
    streak.last_completed_date = today
    db.commit()
