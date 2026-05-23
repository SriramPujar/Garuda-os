import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database import Base, get_db
import app.models as models

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

def get_auth_headers():
    # Register & Login to get token
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "seeker@dharma.org",
            "username": "seeker1",
            "password": "dharmapassword"
        }
    )
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "seeker1", "password": "dharmapassword"}
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# --- SpiritualTube Tests ---
def test_spiritualtube_endpoints():
    headers = get_auth_headers()
    
    # 1. Search videos
    response = client.get("/api/v1/spiritualtube/videos/search?query=gita", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0
    video_id = response.json()[0]["youtube_id"]
    
    # 2. Get video details (which creates it in DB)
    details_res = client.get(f"/api/v1/spiritualtube/videos/{video_id}", headers=headers)
    assert details_res.status_code == 200
    assert details_res.json()["youtube_id"] == video_id
    
    # 3. Add study note
    note_res = client.post(
        f"/api/v1/spiritualtube/videos/{video_id}/notes",
        headers=headers,
        json={"timestamp": 120, "note_text": "Beautiful explanation of the Self"}
    )
    assert note_res.status_code == 200
    assert note_res.json()["timestamp"] == 120
    assert note_res.json()["note_text"] == "Beautiful explanation of the Self"
    
    # 4. Get video notes
    notes_get_res = client.get(f"/api/v1/spiritualtube/videos/{video_id}/notes", headers=headers)
    assert notes_get_res.status_code == 200
    assert len(notes_get_res.json()) > 0
    note_id = notes_get_res.json()[0]["id"]
    
    # 5. Update watching progress
    progress_res = client.post(
        f"/api/v1/spiritualtube/videos/{video_id}/progress",
        headers=headers,
        json={"watched_seconds": 300, "is_completed": False}
    )
    assert progress_res.status_code == 200
    assert progress_res.json()["watched_seconds"] == 300

    # 6. Delete note
    del_res = client.delete(f"/api/v1/spiritualtube/notes/{note_id}", headers=headers)
    assert del_res.status_code == 200
    
    # 7. Get learning paths
    paths_res = client.get("/api/v1/spiritualtube/paths", headers=headers)
    assert paths_res.status_code == 200
    assert len(paths_res.json()) > 0

# --- Nada Tests ---
def test_nada_endpoints():
    headers = get_auth_headers()

    # 1. Get tracks
    tracks_res = client.get("/api/v1/nada/tracks", headers=headers)
    assert tracks_res.status_code == 200
    assert len(tracks_res.json()) > 0
    track_id = tracks_res.json()[0]["id"]

    # 2. Toggle favorite
    fav_res = client.post(f"/api/v1/nada/tracks/{track_id}/favorite", headers=headers)
    assert fav_res.status_code == 200
    assert fav_res.json()["is_favorite"] is True

    # 3. Get favorites
    favs_res = client.get("/api/v1/nada/favorites", headers=headers)
    assert favs_res.status_code == 200
    assert len(favs_res.json()) > 0
    assert favs_res.json()[0]["id"] == track_id

    # 4. Translate lyrics (offline fallback)
    translate_res = client.post(
        "/api/v1/nada/translate-lyrics",
        headers=headers,
        json={"lyrics": "Om Asato Ma Sadgamaya", "deity": "Upanishad"}
    )
    assert translate_res.status_code == 200
    assert "translation" in translate_res.json()

# --- Workspace Tests ---
def test_workspace_endpoints():
    headers = get_auth_headers()

    # 1. Create notes
    note1_res = client.post(
        "/api/v1/workspace/notes",
        headers=headers,
        json={"title": "Vedanta Notes 1", "content": "Contemplation on the non-dual reality.", "category": "Upanishads"}
    )
    assert note1_res.status_code == 200
    n1_id = note1_res.json()["id"]

    note2_res = client.post(
        "/api/v1/workspace/notes",
        headers=headers,
        json={"title": "Gita Ch 2", "content": "Focus on the action itself, not fruits.", "category": "Gita study"}
    )
    assert note2_res.status_code == 200
    n2_id = note2_res.json()["id"]

    # 2. Link notes
    link_res = client.post(
        "/api/v1/workspace/notes/links",
        headers=headers,
        json={"source_note_id": n1_id, "target_note_id": n2_id, "link_type": "ref"}
    )
    assert link_res.status_code == 200
    link_id = link_res.json()["id"]

    # 3. Get graph
    graph_res = client.get("/api/v1/workspace/notes/graph", headers=headers)
    assert graph_res.status_code == 200
    assert len(graph_res.json()["nodes"]) >= 2
    assert len(graph_res.json()["links"]) >= 1

    # 4. Create tasks
    task_res = client.post(
        "/api/v1/workspace/tasks",
        headers=headers,
        json={"title": "Perform morning pranayama", "category": "Meditation", "due_time": "05:15 AM"}
    )
    assert task_res.status_code == 200
    task_id = task_res.json()["id"]

    # 5. Get tasks
    tasks_res = client.get("/api/v1/workspace/tasks", headers=headers)
    assert tasks_res.status_code == 200
    assert len(tasks_res.json()) > 0

    # 6. Complete task
    update_task_res = client.put(
        f"/api/v1/workspace/tasks/{task_id}",
        headers=headers,
        json={"is_completed": True}
    )
    assert update_task_res.status_code == 200
    assert update_task_res.json()["is_completed"] is True

    # 7. Delete task
    del_task_res = client.delete(f"/api/v1/workspace/tasks/{task_id}", headers=headers)
    assert del_task_res.status_code == 200

    # 8. Test bracket links parsing
    note3_res = client.post(
        "/api/v1/workspace/notes",
        headers=headers,
        json={"title": "Atma Vichara", "content": "Contemplate self inquiry as taught in [[Vedanta Notes 1]].", "category": "Self-Inquiry"}
    )
    assert note3_res.status_code == 200
    n3_id = note3_res.json()["id"]
    
    graph_res2 = client.get("/api/v1/workspace/notes/graph", headers=headers)
    assert graph_res2.status_code == 200
    
    links = graph_res2.json()["links"]
    found_link = False
    for link in links:
        if (link["source"] == n1_id and link["target"] == n3_id) or (link["source"] == n3_id and link["target"] == n1_id):
            found_link = True
            break
    assert found_link is True

