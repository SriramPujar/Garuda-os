from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class YoutubeChannel(Base):
    __tablename__ = "youtube_channels"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=False)
    thumbnail_url = Column(String, nullable=True)
    is_verified = Column(Boolean, default=True)  # True = approved for discovery
    last_discovered_at = Column(DateTime, default=datetime.utcnow)

class SpiritualVideo(Base):
    __tablename__ = "spiritual_videos"

    id = Column(Integer, primary_key=True, index=True)
    youtube_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=False)  # Bhagavad Gita, Vedanta, Bhakti, etc.
    tags = Column(String, nullable=True)        # Comma-separated tags
    duration = Column(Integer, default=0)       # Duration in seconds
    thumbnail_url = Column(String, nullable=True)
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    learnings_json = Column(Text, nullable=True) # JSON string: key teachings, verse references, reflection prompts
    timestamps_json = Column(Text, nullable=True) # JSON string: important timestamps & concepts
    
    # Ingestion metadata fields
    views = Column(Integer, default=0)
    publish_date = Column(DateTime, nullable=True)
    chapters_json = Column(Text, nullable=True)  # JSON string of video chapters
    channel_name = Column(String, nullable=True)
    comments_count = Column(Integer, default=0)
    moderation_status = Column(String, default="pending")  # pending, approved, rejected
    is_spiritual = Column(Boolean, default=True)
    
    # Advanced Spiritual Discovery fields
    authenticity_score = Column(Integer, default=0)
    spiritual_tradition = Column(String, nullable=True) # Vaishnavism, Shaivism, Shaktism, Smarta, Advaita, Dvaita, ISKCON, Yoga
    content_type = Column(String, nullable=True)        # lecture, kirtan, bhajan, mantra, meditation, storytelling, ritual, satsang, philosophy, podcast
    energy_type = Column(String, nullable=True)         # calming, devotional, energetic, meditative, intellectual
    speaker_name = Column(String, nullable=True)
    scriptures_referenced = Column(String, nullable=True) # Comma-separated list
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    notes = relationship("VideoNote", back_populates="video", cascade="all, delete-orphan")
    progress = relationship("UserVideoProgress", back_populates="video", cascade="all, delete-orphan")

class VideoNote(Base):
    __tablename__ = "video_notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("spiritual_videos.id"), nullable=False)
    timestamp = Column(Integer, nullable=False)  # Time in seconds
    note_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    video = relationship("SpiritualVideo", back_populates="notes")
    user = relationship("User")

class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=False)
    level = Column(String, default="Beginner")  # Beginner, Intermediate, Advanced
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    videos = relationship("LearningPathVideo", back_populates="path", cascade="all, delete-orphan")

class LearningPathVideo(Base):
    __tablename__ = "learning_path_videos"

    id = Column(Integer, primary_key=True, index=True)
    path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("spiritual_videos.id"), nullable=False)
    sequence = Column(Integer, default=0)

    # Relationships
    path = relationship("LearningPath", back_populates="videos")
    video = relationship("SpiritualVideo")

class UserVideoProgress(Base):
    __tablename__ = "user_video_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("spiritual_videos.id"), nullable=False)
    watched_seconds = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    last_watched = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    video = relationship("SpiritualVideo", back_populates="progress")
    user = relationship("User")
