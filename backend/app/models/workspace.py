from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class SpiritualNote(Base):
    __tablename__ = "spiritual_notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)        # Markdown content
    category = Column(String, nullable=True)     # Gita study, Realization, Temple visit, etc.
    ai_summary = Column(Text, nullable=True)
    tags = Column(String, nullable=True)         # Comma-separated tags
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")

class NoteLink(Base):
    __tablename__ = "note_links"

    id = Column(Integer, primary_key=True, index=True)
    source_note_id = Column(Integer, ForeignKey("spiritual_notes.id", ondelete="CASCADE"), nullable=False)
    target_note_id = Column(Integer, ForeignKey("spiritual_notes.id", ondelete="CASCADE"), nullable=False)
    link_type = Column(String, default="ref")    # ref, expansion, contradiction

    # Relationships
    source = relationship("SpiritualNote", foreign_keys=[source_note_id])
    target = relationship("SpiritualNote", foreign_keys=[target_note_id])

class DharmicTask(Base):
    __tablename__ = "dharmic_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    category = Column(String, nullable=False)     # Chanting, Meditation, Scripture, Seva, Fasting, Ritual
    target_date = Column(Date, nullable=True)
    due_time = Column(String, nullable=True)       # e.g., "05:00 AM" (Brahma Muhurta)
    is_completed = Column(Boolean, default=False)
    repeat_frequency = Column(String, default="none") # none, daily, weekly, ekadashi
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")
