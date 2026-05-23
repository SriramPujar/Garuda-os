from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class SadhanaRoutine(Base):
    __tablename__ = "sadhana_routines"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    routine_type = Column(String, default="japa")  # japa, meditation, scripture, pranayama, puja
    target_value = Column(Integer, default=108)     # count of chants or minutes of meditation
    unit = Column(String, default="counts")          # counts, minutes, chapters
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="sadhana_routines")
    logs = relationship("SadhanaLog", back_populates="routine", cascade="all, delete-orphan")

class SadhanaLog(Base):
    __tablename__ = "sadhana_logs"

    id = Column(Integer, primary_key=True, index=True)
    routine_id = Column(Integer, ForeignKey("sadhana_routines.id"), nullable=False)
    completed_at = Column(DateTime, default=datetime.utcnow)
    value_completed = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    status = Column(String, default="completed")  # completed, partial, skipped

    # Relationships
    routine = relationship("SadhanaRoutine", back_populates="logs")

class SadhanaStreak(Base):
    __tablename__ = "sadhana_streaks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    current_streak = Column(Integer, default=0)
    max_streak = Column(Integer, default=0)
    last_completed_date = Column(Date, nullable=True)
