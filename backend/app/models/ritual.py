from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from datetime import datetime
from app.database import Base

class RitualTemplate(Base):
    __tablename__ = "ritual_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    deity = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    steps_json = Column(Text, nullable=False) # JSON array of step dicts: {step_number: int, name: str, instruction: str, mantra: str}
    offerings_json = Column(Text, nullable=True) # JSON list of required materials
    estimated_duration = Column(Integer, default=15) # minutes

class UserRitualLog(Base):
    __tablename__ = "user_ritual_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ritual_name = Column(String, nullable=False)
    completed_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
    duration_spent = Column(Integer, default=0) # in minutes
