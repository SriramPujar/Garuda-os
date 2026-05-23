import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.nada import SpiritualAudio, UserAudioProgress
from app.config import settings

logger = logging.getLogger("garuda_dharma.nada")

router = APIRouter(prefix="/nada", tags=["nada"])

# --- Pydantic Schemas ---
class TrackOut(BaseModel):
    id: int
    title: str
    artist: str
    url: str
    category: str
    deity: Optional[str]
    lyrics: Optional[str]
    meaning: Optional[str]
    mood_tags: Optional[str]
    spiritual_intensity: int
    is_mantra_loopable: bool
    duration: int

    class Config:
        from_attributes = True

class LyricsTranslateRequest(BaseModel):
    lyrics: str
    deity: Optional[str] = None

# --- Curated Online Tracks ---
CURATED_TRACKS = [
    {
        "title": "Shiva Tandava Stotram",
        "artist": "Traditional Vedic Chants",
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3", # Fallback demo streams
        "category": "Chant",
        "deity": "Shiva",
        "lyrics": "Jata tave gala jala pravaha pavitha sthale...",
        "meaning": "From the forest of His matted locks, water flows and wets His neck...",
        "mood_tags": "energetic, focus, raw",
        "spiritual_intensity": 5,
        "is_mantra_loopable": False,
        "duration": 520
    },
    {
        "title": "Gayatri Mantra (108 Loops)",
        "artist": "Pandit Jasraj",
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
        "category": "Mantra",
        "deity": "Gayatri / Savitr",
        "lyrics": "Om bhur bhuvah svah tat savitur varenyam bhargo devasya dhimahi dhiyo yo nah prachodayat",
        "meaning": "We meditate on the glorious splendor of the Vivifier, the Divine Sun. May He inspire our intelligence.",
        "mood_tags": "calm, focus, morning",
        "spiritual_intensity": 4,
        "is_mantra_loopable": True,
        "duration": 600
    },
    {
        "title": "Hare Krishna Maha Mantra",
        "artist": "Vrindavan Kirtan",
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
        "category": "Kirtan",
        "deity": "Krishna",
        "lyrics": "Hare Krishna Hare Krishna Krishna Krishna Hare Hare, Hare Rama Hare Rama Rama Rama Hare Hare",
        "meaning": "Oh Divine Energy (Hara), Oh All-Attractive Lord (Krishna), Oh Supreme Enjoyer (Rama), please engage me in your devotional service.",
        "mood_tags": "energetic, calm, bhakti",
        "spiritual_intensity": 4,
        "is_mantra_loopable": True,
        "duration": 480
    },
    {
        "title": "Sri Suktam",
        "artist": "Rigveda Chants",
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3",
        "category": "Chant",
        "deity": "Lakshmi",
        "lyrics": "Hiranyavarnam harinim suvarnarajatastrajam...",
        "meaning": "I invoke Sri, the Golden-hued, the beautiful deer adorned with silver and gold garlands...",
        "mood_tags": "calm, focus, abundance",
        "spiritual_intensity": 5,
        "is_mantra_loopable": False,
        "duration": 360
    },
    {
        "title": "Om Chanting",
        "artist": "Himalayan Sadhus",
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3",
        "category": "Meditation",
        "deity": "Brahman",
        "lyrics": "A-U-M",
        "meaning": "The primordial sound of creation, representing the waking, dreaming, and deep sleep states leading to the Turiya (pure consciousness).",
        "mood_tags": "calm, sleep, meditation",
        "spiritual_intensity": 3,
        "is_mantra_loopable": True,
        "duration": 900
    },
    {
        "title": "Shree Hanuman Chalisa",
        "artist": "Hariharan",
        "url": "https://open.spotify.com/track/0U6K212Wv9K7X8dO2t5i2W",
        "category": "Chant",
        "deity": "Hanuman",
        "lyrics": "Shree Guru Charan Saroj Raj Niji Manu Mukur Sudhari...",
        "meaning": "Having cleansed the mirror of my mind with the dust of the lotus feet of Sri Guru...",
        "mood_tags": "energetic, bhakti",
        "spiritual_intensity": 5,
        "is_mantra_loopable": False,
        "duration": 580,
        "audio_source": "spotify",
        "authenticity_score": 95
    },
    {
        "title": "Shiva Tandava Stotram",
        "artist": "Uma Mohan",
        "url": "https://open.spotify.com/track/2rqhFgbbKwnb9MLmUQDhG6",
        "category": "Chant",
        "deity": "Shiva",
        "lyrics": "Jatatavegalajjala pravahapavitasthale...",
        "meaning": "With his neck consecrated by the flow of water that flows from his hair...",
        "mood_tags": "energetic, focus",
        "spiritual_intensity": 5,
        "is_mantra_loopable": False,
        "duration": 480,
        "audio_source": "spotify",
        "authenticity_score": 95
    },
    {
        "title": "Madhurashtakam",
        "artist": "Shreya Ghoshal",
        "url": "https://open.spotify.com/track/1D1Kj7hY37k9vB0vW87jBw",
        "category": "Bhajan",
        "deity": "Krishna",
        "lyrics": "Adharam Madhuram Vadanam Madhuram...",
        "meaning": "His lips are sweet, His face is sweet, His eyes are sweet, His smile is sweet...",
        "mood_tags": "calm, bhakti",
        "spiritual_intensity": 4,
        "is_mantra_loopable": False,
        "duration": 250,
        "audio_source": "spotify",
        "authenticity_score": 90
    },
    {
        "title": "Achyutam Keshavam",
        "artist": "Kaushiki Chakraborty",
        "url": "https://open.spotify.com/track/6rqhFgbbKwnb9MLmUQDhG6",
        "category": "Bhajan",
        "deity": "Krishna",
        "lyrics": "Achyutam Keshavam Rama Narayanam...",
        "meaning": "Who says the Lord does not come? Like Shabari, we do not call him with love...",
        "mood_tags": "calm, bhakti",
        "spiritual_intensity": 4,
        "is_mantra_loopable": False,
        "duration": 340,
        "audio_source": "spotify",
        "authenticity_score": 90
    },
    {
        "title": "Mahamrityunjaya Mantra (108 times)",
        "artist": "Shankar Mahadevan",
        "url": "https://open.spotify.com/track/4uLU6hbiGjLi7t1W7zrjUR",
        "category": "Mantra",
        "deity": "Shiva",
        "lyrics": "Om Tryambakam Yajamahe Sugandhim Pushti-Vardhanam...",
        "meaning": "We worship the three-eyed Lord, who is fragrant and who nourishes all...",
        "mood_tags": "calm, focus, healing",
        "spiritual_intensity": 5,
        "is_mantra_loopable": True,
        "duration": 1800,
        "audio_source": "spotify",
        "authenticity_score": 95
    }
]

# Seed function to populate curated tracks if they don't exist
def seed_tracks_if_empty(db: Session):
    for t in CURATED_TRACKS:
        exists = db.query(SpiritualAudio).filter(SpiritualAudio.title == t["title"]).first()
        if not exists:
            db.add(SpiritualAudio(**t))
    db.commit()

# --- API Endpoints ---

@router.get("/tracks", response_model=List[TrackOut])
def get_tracks(category: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Get all spiritual tracks. Seed default tracks if database is empty.
    """
    seed_tracks_if_empty(db)
    
    query = db.query(SpiritualAudio)
    if category:
        query = query.filter(SpiritualAudio.category == category)
    
    return query.all()

@router.get("/audio/search", response_model=List[TrackOut])
async def search_audio(query: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    """
    Search online/local devotional audio. Dynamically filters and searches based on deity or tags.
    """
    seed_tracks_if_empty(db)
    
    # 1. Local keyword search
    db_results = db.query(SpiritualAudio).filter(
        (SpiritualAudio.title.ilike(f"%{query}%")) |
        (SpiritualAudio.artist.ilike(f"%{query}%")) |
        (SpiritualAudio.deity.ilike(f"%{query}%")) |
        (SpiritualAudio.mood_tags.ilike(f"%{query}%"))
    ).all()
    
    seen_ids = {t.id for t in db_results}
    results = list(db_results)
    
    # 2. Local semantic search
    try:
        from app.core.vector_store import vector_store_service
        semantic_hits = vector_store_service.search_audio(query, limit=5)
        audio_ids = [hit["audio_id"] for hit in semantic_hits]
        if audio_ids:
            semantic_tracks = db.query(SpiritualAudio).filter(SpiritualAudio.id.in_(audio_ids)).all()
            for t in semantic_tracks:
                if t.id not in seen_ids:
                    seen_ids.add(t.id)
                    results.append(t)
    except Exception as e:
        logger.warning(f"Semantic audio search failed: {e}")
        
    # 3. If results count is low, supplement with online Spotify/YouTube results parsed as Audio
    if len(results) < 5:
        try:
            from app.core.spotify_search import spotify_search
            online_tracks = await spotify_search.search_tracks(query)
            
            for t in online_tracks:
                url = t["url"]
                # Skip if already in results
                if any(r.url == url for r in results):
                    continue
                    
                exists = db.query(SpiritualAudio).filter(SpiritualAudio.url == url).first()
                if not exists:
                    audio = SpiritualAudio(
                        title=t["title"],
                        artist=t["artist"],
                        url=url,
                        category=t["category"],
                        deity=t["deity"],
                        lyrics=t.get("lyrics"),
                        meaning=t.get("meaning"),
                        duration=t["duration"],
                        spiritual_intensity=t.get("spiritual_intensity", 4),
                        is_mantra_loopable=t.get("is_mantra_loopable", False),
                        mood_tags=t.get("mood_tags", "calm, bhakti"),
                        audio_source=t.get("audio_source", "spotify"),
                        authenticity_score=t.get("authenticity_score", 80)
                    )
                    db.add(audio)
                    db.commit()
                    db.refresh(audio)
                    results.append(audio)
                else:
                    results.append(exists)
        except Exception as e:
            logger.error(f"Live search supplement failed in /nada/audio/search: {e}")

    # Sort final results: Spotify tracks first, then YouTube/other tracks
    results.sort(key=lambda x: 0 if (getattr(x, "audio_source", "") == "spotify" or (getattr(x, "url", "") and "spotify.com" in getattr(x, "url", ""))) else 1)
                
    return results

@router.get("/tracks/{track_id}", response_model=TrackOut)
def get_track_details(track_id: int, db: Session = Depends(get_db)):
    track = db.query(SpiritualAudio).filter(SpiritualAudio.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track

@router.post("/tracks/{track_id}/favorite")
def toggle_favorite(
    track_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    track = db.query(SpiritualAudio).filter(SpiritualAudio.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
        
    progress = db.query(UserAudioProgress).filter(
        UserAudioProgress.audio_id == track_id,
        UserAudioProgress.user_id == current_user.id
    ).first()
    
    if not progress:
        progress = UserAudioProgress(
            user_id=current_user.id,
            audio_id=track_id,
            is_favorite=True
        )
        db.add(progress)
    else:
        progress.is_favorite = not progress.is_favorite
        
    db.commit()
    return {"status": "success", "is_favorite": progress.is_favorite}

@router.get("/favorites", response_model=List[TrackOut])
def get_favorites(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    favorites = db.query(SpiritualAudio).join(
        UserAudioProgress, UserAudioProgress.audio_id == SpiritualAudio.id
    ).filter(
        UserAudioProgress.user_id == current_user.id,
        UserAudioProgress.is_favorite == True
    ).all()
    return favorites

@router.post("/translate-lyrics")
async def translate_lyrics(req: LyricsTranslateRequest, current_user: User = Depends(get_current_user)):
    """
    Translates Sanskrit/Hindi devotional lyrics word-by-word into English with spiritual commentary.
    """
    prompt = f"""
    Translate the following devotional lyrics. Break down the key Sanskrit/spiritual terms word-by-word and provide their inner spiritual meaning.
    Lyrics: {req.lyrics}
    Deity Context: {req.deity or 'Hindu Deity'}

    Format your output clearly:
    1. Line-by-Line Translation
    2. Word Breakdown (for important spiritual terms)
    3. Inner Meaning / Mystical significance of the chant
    """
    
    # Try calling Ollama
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.3}
    }
    
    try:
        import sys
        import os
        timeout_val = 1.0 if ("pytest" in sys.modules or os.getenv("TESTING") == "true") else 30.0
        async with httpx.AsyncClient(timeout=timeout_val) as client:
            response = await client.post(f"{settings.OLLAMA_BASE_URL}/api/chat", json=payload)
            if response.status_code == 200:
                res_data = response.json()
                return {"translation": res_data.get("message", {}).get("content", "").strip()}
    except Exception as e:
        logger.error(f"Error calling Ollama for lyrics translation: {str(e)}")
        
    # Fallback
    return {
        "translation": (
            f"**[Offline Fallback translation]**\n\n"
            f"Lyrics: {req.lyrics}\n\n"
            f"Word breakdown: 'Om' is the primordial vibration. 'Savitur' refers to the sun / giver of life. "
            f"'Bhargo' means divine radiance.\n\n"
            f"Connection to Ollama failed. Please ensure the local LLM is pulled and running to generate deep breakdowns."
        )
    }

# --- Playlists & Semantic Endpoints ---

@router.get("/playlists/recommended")
def get_recommended_playlists(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.nada import AudioPlaylist
    playlist_count = db.query(AudioPlaylist).count()
    if playlist_count == 0:
        seed_tracks_if_empty(db)
        from app.core.audio_ingestion import audio_ingestion_service
        audio_ingestion_service.generate_playlists(db)

    from app.core.recommendation import recommendation_engine
    recs = recommendation_engine.recommend_for_user(current_user.id, db)
    state = recs["state"]
    explanation = recs["explanation"]
    
    target_playlist = "Brahma Muhurta"
    if state == "mentally overloaded":
        target_playlist = "Brahma Muhurta"
    elif state == "emotionally disturbed":
        target_playlist = "Bhakti Kirtan"
    elif state == "distracted":
        target_playlist = "Shiva Meditation"
        
    playlist = db.query(AudioPlaylist).filter(AudioPlaylist.name == target_playlist).first()
    if not playlist:
        playlist = db.query(AudioPlaylist).first()
        
    all_playlists = db.query(AudioPlaylist).all()
    
    return {
        "active_state": state,
        "explanation": explanation,
        "recommended_playlist_id": playlist.id if playlist else None,
        "playlists": all_playlists
    }

@router.get("/playlists/{playlist_id}/tracks", response_model=List[TrackOut])
def get_playlist_tracks(playlist_id: int, db: Session = Depends(get_db)):
    from app.models.nada import AudioPlaylistTrack
    tracks = db.query(SpiritualAudio).join(
        AudioPlaylistTrack, AudioPlaylistTrack.audio_id == SpiritualAudio.id
    ).filter(
        AudioPlaylistTrack.playlist_id == playlist_id
    ).order_by(AudioPlaylistTrack.sequence.asc()).all()
    
    return tracks

@router.get("/audio/search/semantic", response_model=List[TrackOut])
def semantic_search_audio(query: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    from app.core.vector_store import vector_store_service
    results = vector_store_service.search_audio(query, limit=10)
    
    audio_ids = [hit["audio_id"] for hit in results]
    tracks = db.query(SpiritualAudio).filter(SpiritualAudio.id.in_(audio_ids)).all()
    
    track_map = {t.id: t for t in tracks}
    ordered_tracks = [track_map[aid] for aid in audio_ids if aid in track_map]
    
    return ordered_tracks
