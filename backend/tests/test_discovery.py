import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os
import json
from unittest.mock import patch, AsyncMock, MagicMock

# Adjust path to include the backend folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database import Base, get_db
# Import app.models to ensure ALL database models are registered on Base
import app.models as models

# Core services imports
from app.core.multilingual import multilingual_expansion_service
from app.core.crawl_manager import crawl_manager
from app.core.search_engine import search_engine

# Use the same test SQLite database to prevent shared pytest dependency overrides conflicts
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
    # Setup database before each test
    Base.metadata.create_all(bind=engine)
    yield
    # Teardown database after each test
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    try:
        if os.path.exists("./test_garuda.db"):
            os.remove("./test_garuda.db")
    except PermissionError:
        pass

def get_auth_headers():
    # Register & Login to get token
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "discovery_seeker@dharma.org",
            "username": "discovery_seeker",
            "password": "dharmapassword"
        }
    )
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "discovery_seeker", "password": "dharmapassword"}
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# --- 1. Multilingual Expansion Service Tests ---
def test_multilingual_expansion():
    # Test dictionary-based query expansion
    expanded = multilingual_expansion_service.expand_from_dict("krishna bhajan")
    assert len(expanded) > 0
    # Must contain Sanskrit "कृष्ण भजनम्" and Hindi "कृष्णा भजन"
    assert any("कृष्ण भजनम्" in q for q in expanded)
    assert any("कृष्णा भजन" in q for q in expanded)

    # Test dictionary expansion with words that don't match
    empty_expanded = multilingual_expansion_service.expand_from_dict("random search term")
    assert len(empty_expanded) == 0

    # Test LLM-based query translation fallback
    async def run_llm_test():
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json = MagicMock(return_value={"response": '["शिव भजन", "சிவன் பஜனை"]'})
            mock_post.return_value = mock_response

            translations = await multilingual_expansion_service.translate_query_via_llm("shiva bhajan")
            assert "शिव भजन" in translations
            assert "சிவன் பஜனை" in translations

            # Test expand_query method fallback to LLM
            expanded_all = await multilingual_expansion_service.expand_query("durga stotram")
            assert "शिव भजन" in expanded_all
            assert "durga stotram" in expanded_all

    asyncio.run(run_llm_test())

# --- 2. Crawl Queue & Processing Tests ---
def test_crawl_queue_and_manager():
    db = TestingSessionLocal()
    try:
        async def run_crawl_test():
            # Add seed URL to queue
            url = "https://www.youtube.com/channel/UCsT0YIqwnpJb-cQ"
            added = await crawl_manager.add_to_queue(url, "youtube_channel", db)
            assert added is True

            # Duplicates must not be added
            added_dup = await crawl_manager.add_to_queue(url, "youtube_channel", db)
            assert added_dup is False

            # Verify added to DB
            item = db.query(models.CrawlQueue).filter(models.CrawlQueue.url == url).first()
            assert item is not None
            assert item.status == "pending"
            assert item.source_type == "youtube_channel"

            # Mock the network fetch for _crawl_youtube_channel
            rss_mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
            <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns:media="http://search.yahoo.com/mrss/" xmlns="http://www.w3.org/2005/Atom">
              <link rel="alternative" href="https://www.youtube.com/channel/UCsT0YIqwnpJb-cQ"/>
              <title>Vedanta Society</title>
              <entry>
                <id>yt:video:test_crawl_vid_01</id>
                <yt:videoId>test_crawl_vid_01</yt:videoId>
                <title>Gita Discourse Chapter 2: Swami Sarvapriyananda</title>
                <published>2026-05-22T05:00:00+00:00</published>
                <author>
                  <name>Vedanta Society</name>
                </author>
                <media:group>
                  <media:title>Gita Chapter 2</media:title>
                  <media:description>Discourse on Bhagavad Gita Chapter 2 by Swami Sarvapriyananda</media:description>
                  <media:thumbnail url="https://img.youtube.com/vi/test_crawl_vid_01/0.jpg"/>
                  <media:community>
                    <media:statistics views="5000"/>
                  </media:community>
                </media:group>
              </entry>
            </feed>
            """

            with patch("httpx.AsyncClient.get") as mock_get:
                mock_res = MagicMock()
                mock_res.status_code = 200
                mock_res.text = rss_mock_xml
                mock_get.return_value = mock_res

                # Process the next queue item
                success = await crawl_manager.process_next_queue_item(db)
                assert success is True

                # Verify queue item status updated
                db.refresh(item)
                assert item.status == "completed"

                # Verify video imported to DB
                vid = db.query(models.SpiritualVideo).filter(models.SpiritualVideo.youtube_id == "test_crawl_vid_01").first()
                assert vid is not None
                assert vid.title == "Gita Discourse Chapter 2: Swami Sarvapriyananda"
                assert vid.views == 5000

                # Verify CrawlHistory log created
                history = db.query(models.CrawlHistory).filter(models.CrawlHistory.url == url).first()
                assert history is not None
                assert history.status == "success"
                assert history.discovered_count == 1

        asyncio.run(run_crawl_test())
    finally:
        db.close()

# --- 3. Hybrid Search & Graph Boosting Tests ---
def test_hybrid_search_engine():
    db = TestingSessionLocal()
    try:
        async def run_search_test():
            # Seed test videos
            v1 = models.SpiritualVideo(
                youtube_id="vid_111",
                title="Sanskrit Chanting of Shiva Sahasranama",
                description="Beautiful calming Shiva chants in Sanskrit",
                category="Chant",
                is_spiritual=True,
                moderation_status="approved",
                authenticity_score=95,
                spiritual_tradition="Shaivism",
                content_type="chant",
                energy_type="calming"
            )
            v2 = models.SpiritualVideo(
                youtube_id="vid_222",
                title="Introduction to Advaita Vedanta philosophy",
                description="Deep lecture on Upanishads and non-duality",
                category="Philosophy",
                is_spiritual=True,
                moderation_status="approved",
                authenticity_score=90,
                spiritual_tradition="Advaita",
                content_type="lecture",
                energy_type="intellectual"
            )
            db.add_all([v1, v2])
            db.commit()

            # Seed knowledge graph nodes and relationships
            # Deity Node: Shiva
            n_shiva = models.GraphNode(name="Shiva", node_type="deity", description="A Hindu deity")
            # Video Node: corresponding to v1
            n_v1 = models.GraphNode(name="Sanskrit Chanting of Shiva Sahasranama", node_type="video", description="Video track")
            db.add_all([n_shiva, n_v1])
            db.commit()

            rel = models.GraphRelationship(
                source_node_id=n_shiva.id,
                target_node_id=n_v1.id,
                relationship_type="references",
                weight=1.5
            )
            db.add(rel)
            db.commit()

            # Perform hybrid search with query "shiva" and expand=True
            results = await search_engine.hybrid_search_videos(db, "shiva", expand=True)
            assert len(results) > 0
            
            # Shiva chanting video should be first due to matching title keyword and graph boost
            assert results[0]["youtube_id"] == "vid_111"
            assert results[0]["spiritual_tradition"] == "Shaivism"
            assert results[0]["search_score"] > 0

            # Test filters (tradition filter = Advaita)
            results_advaita = await search_engine.hybrid_search_videos(db, "philosophy", tradition="Advaita")
            assert len(results_advaita) == 1
            assert results_advaita[0]["youtube_id"] == "vid_222"

            # Test authenticity filter
            results_auth = await search_engine.hybrid_search_videos(db, "Shiva", min_authenticity=92)
            assert len(results_auth) == 1
            assert results_auth[0]["youtube_id"] == "vid_111"

        asyncio.run(run_search_test())
    finally:
        db.close()

# --- 4. API Endpoint Integration Tests ---
def test_discovery_api_endpoints():
    headers = get_auth_headers()

    # 1. Add crawl seed URL
    add_res = client.post(
        "/api/v1/discovery/queue/add",
        headers=headers,
        json={
            "url": "https://www.youtube.com/playlist?list=PL22E423E11",
            "source_type": "youtube_playlist",
            "priority": 2
        }
    )
    assert add_res.status_code == 200
    assert add_res.json()["status"] == "success"

    # 2. Get Queue status
    status_res = client.get("/api/v1/discovery/queue/status", headers=headers)
    assert status_res.status_code == 200
    assert "queue_stats" in status_res.json()
    assert status_res.json()["queue_stats"]["pending"] >= 1

    # 3. Trigger crawler manually
    trigger_res = client.post("/api/v1/discovery/queue/trigger", headers=headers)
    assert trigger_res.status_code == 200
    assert trigger_res.json()["status"] == "success"

    # 4. Fetch Knowledge Graph
    db = TestingSessionLocal()
    try:
        n1 = models.GraphNode(name="Krishna", node_type="deity")
        n2 = models.GraphNode(name="Bhagavad Gita", node_type="scripture")
        db.add_all([n1, n2])
        db.commit()
        
        rel = models.GraphRelationship(source_node_id=n1.id, target_node_id=n2.id, relationship_type="teaches")
        db.add(rel)
        db.commit()
    finally:
        db.close()

    graph_res = client.get("/api/v1/discovery/graph", headers=headers)
    assert graph_res.status_code == 200
    graph_data = graph_res.json()
    assert "nodes" in graph_data
    assert "links" in graph_data
    assert len(graph_data["nodes"]) >= 2
    assert len(graph_data["links"]) >= 1

    # 5. Search Videos API Endpoint
    search_vid_res = client.get("/api/v1/discovery/search/videos?query=Gita", headers=headers)
    assert search_vid_res.status_code == 200
    assert isinstance(search_vid_res.json(), list)

    # 6. Search Audio API Endpoint
    search_aud_res = client.get("/api/v1/discovery/search/audio?query=Chant", headers=headers)
    assert search_aud_res.status_code == 200
    assert isinstance(search_aud_res.json(), list)
