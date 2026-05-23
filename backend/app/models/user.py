from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sadhana_routines = relationship("SadhanaRoutine", back_populates="user", cascade="all, delete-orphan")
    journal_entries = relationship("JournalEntry", back_populates="user", cascade="all, delete-orphan")
    memories = relationship("SpiritualMemory", back_populates="user", cascade="all, delete-orphan")

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    full_name = Column(String, nullable=True)
    
    # Spiritual identity fields
    deity_preference = Column(String, default="Ganesha") # e.g. Ganesha, Krishna, Shiva, Devi
    philosophy_preference = Column(String, default="Advaita") # e.g. Advaita, Dvaita, Vishishtadvaita, Yoga, Bhakti
    spiritual_goals = Column(Text, nullable=True)
    preferred_language = Column(String, default="en") # en, sa, hi
    
    # Relationships
    user = relationship("User", back_populates="profile")
