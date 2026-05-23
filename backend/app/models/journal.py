from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    prompt_used = Column(String, nullable=True) # AI-generated prompt if any
    
    # Emotional/Spiritual State features extracted by agents
    sentiment_score = Column(Float, default=0.0) # -1 to 1 (negative to positive)
    dominant_emotion = Column(String, default="neutral") # calm, anxious, distracted, overloaded, sad, happy, etc.
    reflection_depth = Column(Integer, default=1) # scale 1-5
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="journal_entries")
