from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class SpiritualMemory(Base):
    __tablename__ = "spiritual_memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Types: identity, behavioral, knowledge, emotional, sadhana
    memory_type = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    
    # Vector ID in Qdrant (to fetch/update easily)
    vector_id = Column(String, nullable=True, index=True)
    
    # Extra tags stored as JSON: {"deity": "Shiva", "importance": "high"}
    metadata_json = Column(String, default="{}")
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="memories")
