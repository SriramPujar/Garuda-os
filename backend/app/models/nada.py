from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class SpiritualAudio(Base):
    __tablename__ = "spiritual_audio"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    url = Column(String, nullable=False)        # Online stream URL (e.g. YouTube stream or direct mp3)
    category = Column(String, nullable=False)   # Bhajan, Kirtan, Mantra, Chant, Meditation, Temple Recording
    deity = Column(String, nullable=True)       # Shiva, Krishna, Devi, Ganesha, etc.
    lyrics = Column(Text, nullable=True)
    meaning = Column(Text, nullable=True)
    mood_tags = Column(String, nullable=True)   # Comma-separated (e.g. calm, focus, energetic, sleep)
    spiritual_intensity = Column(Integer, default=1) # 1 to 5 scale
    is_mantra_loopable = Column(Boolean, default=False)
    duration = Column(Integer, default=0)       # In seconds
    
    # New audio ingestion fields
    album = Column(String, nullable=True)
    language = Column(String, nullable=True)
    release_year = Column(Integer, nullable=True)
    audio_source = Column(String, default="youtube") # youtube, spotify, archive_org
    energy_level = Column(String, nullable=True)     # calming, energetic
    sacred_atmosphere = Column(String, nullable=True)# temple, meditation, kirtan
    transliteration = Column(Text, nullable=True)
    
    # Advanced Spiritual Discovery fields
    authenticity_score = Column(Integer, default=0)
    spiritual_tradition = Column(String, nullable=True) # Vaishnavism, Shaivism, Shaktism, Smarta, Advaita, Dvaita, ISKCON, Yoga
    lyrics_translation = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    progress = relationship("UserAudioProgress", back_populates="audio", cascade="all, delete-orphan")

class AudioPlaylist(Base):
    __tablename__ = "audio_playlists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=False)       # Brahma Muhurta, Deep Meditation, Shiva Meditation, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tracks = relationship("AudioPlaylistTrack", back_populates="playlist", cascade="all, delete-orphan")

class AudioPlaylistTrack(Base):
    __tablename__ = "audio_playlist_tracks"

    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("audio_playlists.id"), nullable=False)
    audio_id = Column(Integer, ForeignKey("spiritual_audio.id"), nullable=False)
    sequence = Column(Integer, default=0)

    # Relationships
    playlist = relationship("AudioPlaylist", back_populates="tracks")
    audio = relationship("SpiritualAudio")

class UserAudioProgress(Base):
    __tablename__ = "user_audio_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    audio_id = Column(Integer, ForeignKey("spiritual_audio.id"), nullable=False)
    is_favorite = Column(Boolean, default=False)
    last_played = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    audio = relationship("SpiritualAudio", back_populates="progress")
    user = relationship("User")
