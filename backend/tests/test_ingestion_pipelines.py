import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os
import shutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database import Base, get_db
from app.models.spiritualtube import YoutubeChannel, SpiritualVideo
from app.models.nada import SpiritualAudio, AudioPlaylist, AudioPlaylistTrack
from app.models.user import User
from app.core.moderation import spiritual_moderator
from app.core.vector_store import vector_store_service
from app.core.youtube_ingestion import parse_youtube_rss
from app.core.audio_ingestion import audio_ingestion_service
from app.core.recommendation import recommendation_engine

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_garuda.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    try:
        if os.path.exists("./test_garuda.db"):
            os.remove("./test_garuda.db")
    except PermissionError:
        pass
    
    # Clean up test Qdrant local path if created
    qdrant_test_dir = "d:/P/OS/backend/app/data/qdrant_db"
    # Note: We won't wipe the actual DB, but for unit tests we can mock or keep it

def get_auth_headers():
    # Register & Login to get token
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "devotee@dharma.org",
            "username": "devotee1",
            "password": "dharmapassword"
        }
    )
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "devotee1", "password": "dharmapassword"}
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# 1. Moderation tests
def test_spiritual_moderator():
    # Test fast keyword blocklist
    assert spiritual_moderator.fast_filter("My awesome minecraft gameplay!", "") is False
    assert spiritual_moderator.fast_filter("Bollywood hot gossip and dating scandal", "") is False
    assert spiritual_moderator.fast_filter("Advaita Vedanta Discourse on Upanishads", "") is True

    # Test keyword heuristics fallback (if Ollama is offline or for quick checks)
    # The check_relevance_ollama will fallback to keyword heuristics if post fails
    # Let's test that "Bhagavad Gita commentary" passes the moderation fallback
    assert spiritual_moderator.moderate("Bhagavad Gita commentary", "Verse by verse breakdown of chapter 2") is True

# 2. Vector Store tests
def test_vector_store():
    # Upsert a dummy video
    vector_store_service.upsert_video(
        video_id=999,
        youtube_id="dummy_yt_123",
        title="Contemplation on the Self",
        description="Deep dive into Upanishads",
        transcript="Brahman is the truth, the world is an illusion",
        category="Vedanta",
        deity="Brahman"
    )

    # Search video
    results = vector_store_service.search_videos("Brahman", limit=1)
    assert len(results) > 0
    assert results[0]["video_id"] == 999
    assert results[0]["title"] == "Contemplation on the Self"

    # Upsert a dummy audio
    vector_store_service.upsert_audio(
        audio_id=888,
        title="Shiva Tandava Stotram",
        artist="Traditional priests",
        category="Chant",
        deity="Shiva",
        lyrics="Jata tave gala jala"
    )

    # Search audio
    audio_results = vector_store_service.search_audio("Shiva", limit=1)
    assert len(audio_results) > 0
    assert audio_results[0]["audio_id"] == 888
    assert audio_results[0]["title"] == "Shiva Tandava Stotram"

# 3. YouTube RSS parsing tests
def test_youtube_rss_parser():
    sample_rss = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns:media="http://search.yahoo.com/mrss/" xmlns="http://www.w3.org/2005/Atom">
      <link rel="alternative" href="https://www.youtube.com/channel/UCxxxx"/>
      <title>Spiritual Channel</title>
      <entry>
        <id>yt:video:7QhZf1eQkF4</id>
        <yt:videoId>7QhZf1eQkF4</yt:videoId>
        <title>Yoga of Action: Swami Sarvapriyananda</title>
        <published>2026-05-22T05:00:00+00:00</published>
        <author>
          <name>Vedanta Society</name>
        </author>
        <media:group>
          <media:title>Yoga of Action</media:title>
          <media:description>Discourse on Bhagavad Gita Chapter 2</media:description>
          <media:thumbnail url="https://img.youtube.com/vi/7QhZf1eQkF4/0.jpg"/>
          <media:community>
            <media:statistics views="9876"/>
          </media:community>
        </media:group>
      </entry>
    </feed>
    """
    videos = parse_youtube_rss(sample_rss)
    assert len(videos) == 1
    assert videos[0]["youtube_id"] == "7QhZf1eQkF4"
    assert videos[0]["title"] == "Yoga of Action: Swami Sarvapriyananda"
    assert videos[0]["views"] == 9876
    assert videos[0]["channel_name"] == "Vedanta Society"

# 4. Playlist auto-generation and recommendations
def test_playlist_generation_and_recommendations():
    db = TestingSessionLocal()
    try:
        # Register a test user
        user = User(email="user@sadhana.net", username="user1", hashed_password="hashed_pw")
        db.add(user)
        db.commit()
        db.refresh(user)

        # Seed some spiritual audio
        audio1 = SpiritualAudio(
            title="Morning Vishnu Sahasranamam",
            artist="M.S. Subbulakshmi",
            url="http://example.com/vishnu.mp3",
            category="Chant",
            deity="Vishnu",
            mood_tags="calm, morning",
            energy_level="calming"
        )
        audio2 = SpiritualAudio(
            title="Hara Hara Mahadev",
            artist="Kailash Kher",
            url="http://example.com/shiva.mp3",
            category="Kirtan",
            deity="Shiva",
            mood_tags="energetic, raw",
            energy_level="energetic"
        )
        db.add(audio1)
        db.add(audio2)
        db.commit()

        # Run playlist auto generator
        audio_ingestion_service.generate_playlists(db)

        # Verify playlists created
        playlists = db.query(AudioPlaylist).all()
        assert len(playlists) >= 3
        
        # Verify tracks in Shiva Meditation
        shiva_pl = db.query(AudioPlaylist).filter(AudioPlaylist.name == "Shiva Meditation").first()
        assert shiva_pl is not None
        tracks = db.query(AudioPlaylistTrack).filter(AudioPlaylistTrack.playlist_id == shiva_pl.id).all()
        assert len(tracks) > 0
        
        # Test Recommendations Engine
        recs = recommendation_engine.recommend_for_user(user.id, db)
        assert "state" in recs
        assert "recommended_videos" in recs
        assert "recommended_tracks" in recs
    finally:
        db.close()

# 5. API endpoint tests
def test_api_endpoints():
    headers = get_auth_headers()

    # Register Channel
    reg_response = client.post(
        "/api/v1/spiritualtube/channels/register",
        headers=headers,
        json={
            "channel_id": "UCsT0YIqwnpJb-cQ",
            "title": "Vedanta Society of New York",
            "category": "Vedanta",
            "description": "Spiritual discourses"
        }
    )
    assert reg_response.status_code == 200
    assert reg_response.json()["channel_id"] == "UCsT0YIqwnpJb-cQ"

    # Trigger Ingestion
    trigger_response = client.post("/api/v1/spiritualtube/ingest/trigger", headers=headers)
    assert trigger_response.status_code == 200
    assert "triggered" in trigger_response.json()["message"]

    # Recommended playlists
    pl_response = client.get("/api/v1/nada/playlists/recommended", headers=headers)
    assert pl_response.status_code == 200
    assert "playlists" in pl_response.json()
    playlist_id = pl_response.json()["playlists"][0]["id"]

    # Playlist tracks
    tracks_response = client.get(f"/api/v1/nada/playlists/{playlist_id}/tracks", headers=headers)
    assert tracks_response.status_code == 200
