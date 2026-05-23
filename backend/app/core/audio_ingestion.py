import logging
import httpx
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import os

from app.config import settings
from app.models.nada import SpiritualAudio, AudioPlaylist, AudioPlaylistTrack
from app.core.vector_store import vector_store_service

logger = logging.getLogger("garuda_dharma.audio_ingestion")

class AudioIngestionService:
    def __init__(self):
        # We can configure Spotify Client if keys are available in env
        self.spotify_client_id = os.getenv("SPOTIPY_CLIENT_ID")
        self.spotify_client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
        self.spotify_token = None

    async def fetch_archive_org_tracks(self, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Queries Archive.org search API to retrieve public domain Hindu devotional and Sanskrit audio recordings.
        """
        query = "subject:(bhajan OR kirtan OR veda OR mantra OR upanishad OR sanskrit) AND mediatype:audio"
        url = f"https://archive.org/advancedsearch.php"
        params = {
            "q": query,
            "fl[]": ["identifier", "title", "creator", "subject", "description", "length"],
            "sort[]": ["downloads desc"],
            "rows": limit,
            "output": "json"
        }
        
        tracks = []
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(url, params=params)
                if r.status_code != 200:
                    logger.error(f"Failed to fetch Archive.org search: status {r.status_code}")
                    return []
                
                data = r.json()
                docs = data.get("response", {}).get("docs", [])
                
                for doc in docs:
                    identifier = doc.get("identifier")
                    if not identifier:
                        continue
                    
                    # Fetch file metadata to get the actual MP3 filename
                    meta_url = f"https://archive.org/metadata/{identifier}"
                    meta_r = await client.get(meta_url)
                    if meta_r.status_code != 200:
                        continue
                    
                    meta_data = meta_r.json()
                    files = meta_data.get("files", [])
                    
                    # Find first mp3 file
                    mp3_file = None
                    for f in files:
                        name = f.get("name", "")
                        fmt = f.get("format", "")
                        if name.endswith(".mp3") and ("MP3" in fmt or "VBR MP3" in fmt):
                            mp3_file = name
                            break
                            
                    if not mp3_file:
                        continue
                        
                    stream_url = f"https://archive.org/download/{identifier}/{mp3_file}"
                    
                    # Deduce metadata
                    title = doc.get("title", "Sanskrit Chant")
                    artist = doc.get("creator", "Traditional Devotional")
                    if isinstance(artist, list):
                        artist = artist[0] if artist else "Traditional Devotional"
                    
                    subject_list = doc.get("subject", [])
                    if isinstance(subject_list, str):
                        subject_list = [subject_list]
                    subject_str = " ".join(subject_list).lower()
                    
                    description = doc.get("description", "")
                    if isinstance(description, list):
                        description = " ".join(description)
                    description = description or ""

                    # Strict non-Hindu/non-devotional blocklist check
                    banned_words = ["quran", "qur'an", "bible", "church", "allah", "jesus", "christ", "islam", "koran", "mosque", "gospel", "hymn", "sermon"]
                    title_lower = title.lower()
                    artist_lower = artist.lower()
                    desc_lower = description.lower()
                    if any(bw in title_lower or bw in artist_lower or bw in subject_str or bw in desc_lower for bw in banned_words):
                        logger.info(f"Audio Ingestion Filter: Skipping '{title}' by '{artist}' due to non-Hindu keyword match.")
                        continue
                    
                    # Category deduction
                    category = "Chant"
                    if "bhajan" in title.lower() or "bhajan" in subject_str:
                        category = "Bhajan"
                    elif "kirtan" in title.lower() or "kirtan" in subject_str:
                        category = "Kirtan"
                    elif "mantra" in title.lower() or "mantra" in subject_str:
                        category = "Mantra"
                    elif "veda" in title.lower() or "veda" in subject_str:
                        category = "Chant"
                    
                    # Deity deduction
                    deity = "None"
                    deities = ["Shiva", "Krishna", "Rama", "Devi", "Ganesha", "Hanuman", "Narayana"]
                    for d in deities:
                        if d.lower() in title.lower() or d.lower() in subject_str:
                            deity = d
                            break
                    
                    # Mood tags
                    mood_tags = "calm, meditation"
                    if category in ["Bhajan", "Kirtan"]:
                        mood_tags = "energetic, bhakti, focus"
                    elif deity == "Shiva":
                        mood_tags = "calm, intense, meditation"
                    
                    # Duration
                    duration_sec = 180
                    len_str = doc.get("length")
                    if len_str:
                        try:
                            # length can be in format MM:SS or float seconds
                            if ":" in str(len_str):
                                parts = str(len_str).split(":")
                                if len(parts) == 2:
                                    duration_sec = int(parts[0]) * 60 + int(parts[1])
                            else:
                                duration_sec = int(float(len_str))
                        except Exception:
                            pass
                            
                    tracks.append({
                        "title": title,
                        "artist": artist,
                        "url": stream_url,
                        "category": category,
                        "deity": deity,
                        "lyrics": description[:1000],
                        "meaning": "Public domain devotional track from Archive.org",
                        "mood_tags": mood_tags,
                        "spiritual_intensity": 3 if deity != "None" else 2,
                        "duration": duration_sec,
                        "audio_source": "archive_org",
                        "energy_level": "energetic" if "energetic" in mood_tags else "calming",
                        "sacred_atmosphere": "temple" if category == "Bhajan" else "meditation"
                    })
        except Exception as e:
            logger.error(f"Error fetching Archive.org audio tracks: {e}")
            
        return tracks

    async def ingest_audio_library(self, db: Session, limit: int = 15):
        """
        Discovers and ingests audio tracks, upserting to SQLite and Qdrant.
        """
        logger.info("Starting Audio Ingestion Pipeline")
        tracks = await self.fetch_archive_org_tracks(limit=limit)
        
        ingested_count = 0
        for track in tracks:
            # Check if url already exists
            exists = db.query(SpiritualAudio).filter(SpiritualAudio.url == track["url"]).first()
            if exists:
                continue
                
            audio = SpiritualAudio(
                title=track["title"],
                artist=track["artist"],
                url=track["url"],
                category=track["category"],
                deity=track["deity"],
                lyrics=track["lyrics"],
                meaning=track["meaning"],
                mood_tags=track["mood_tags"],
                spiritual_intensity=track["spiritual_intensity"],
                duration=track["duration"],
                audio_source=track["audio_source"],
                energy_level=track["energy_level"],
                sacred_atmosphere=track["sacred_atmosphere"]
            )
            db.add(audio)
            db.commit()
            db.refresh(audio)
            
            ingested_count += 1
            
            # Index in vector store
            try:
                vector_store_service.upsert_audio(
                    audio_id=audio.id,
                    title=audio.title,
                    artist=audio.artist,
                    category=audio.category,
                    deity=audio.deity,
                    lyrics=audio.lyrics or ""
                )
            except Exception as e:
                logger.error(f"Failed to upsert audio {audio.id} to vector store: {e}")
                
        logger.info(f"Successfully ingested {ingested_count} new audio tracks.")
        
        # Re-generate auto playlists
        self.generate_playlists(db)
        return ingested_count

    def generate_playlists(self, db: Session):
        """
        Auto-generates recommended playlists based on time/mood/deity.
        """
        logger.info("Generating/updating default spiritual playlists.")
        playlists_config = [
            ("Brahma Muhurta", "Morning chanting and peaceful Vedic mantras for spiritual focus.", "morning"),
            ("Shiva Meditation", "Deep, intense meditations and chants dedicated to Bhagavan Shiva.", "meditation"),
            ("Bhakti Kirtan", "Vibrant, heart-opening bhajans and kirtans praising the Divine.", "kirtan")
        ]
        
        for name, desc, cat in playlists_config:
            playlist = db.query(AudioPlaylist).filter(AudioPlaylist.name == name).first()
            if not playlist:
                playlist = AudioPlaylist(
                    name=name,
                    description=desc,
                    category=cat
                )
                db.add(playlist)
                db.commit()
                db.refresh(playlist)
                
            # Fetch matching tracks from DB
            tracks = []
            if name == "Brahma Muhurta":
                tracks = db.query(SpiritualAudio).filter(
                    (SpiritualAudio.category.in_(["Mantra", "Chant"])) |
                    (SpiritualAudio.energy_level == "calming")
                ).limit(10).all()
            elif name == "Shiva Meditation":
                tracks = db.query(SpiritualAudio).filter(
                    (SpiritualAudio.deity == "Shiva") |
                    (SpiritualAudio.title.like("%Shiva%"))
                ).limit(10).all()
            elif name == "Bhakti Kirtan":
                tracks = db.query(SpiritualAudio).filter(
                    SpiritualAudio.category.in_(["Bhajan", "Kirtan"])
                ).limit(10).all()
                
            # If we don't have enough tracks, fall back to any track to seed playlist
            if not tracks:
                tracks = db.query(SpiritualAudio).limit(5).all()

            # Remove previous tracks and fill new ones
            db.query(AudioPlaylistTrack).filter(AudioPlaylistTrack.playlist_id == playlist.id).delete()
            for idx, track in enumerate(tracks):
                pt = AudioPlaylistTrack(
                    playlist_id=playlist.id,
                    audio_id=track.id,
                    sequence=idx + 1
                )
                db.add(pt)
                
            db.commit()
            logger.info(f"Playlist '{name}' populated with {len(tracks)} tracks.")

audio_ingestion_service = AudioIngestionService()
