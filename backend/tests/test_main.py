import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Adjust path to include the backend folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database import Base, get_db

# Create test SQLite database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_garuda.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override database dependency for testing
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

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_register_and_login():
    # Register
    reg_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@seeker.org",
            "username": "testseeker",
            "password": "securepassword",
            "deity_preference": "Shiva",
            "philosophy_preference": "Advaita"
        }
    )
    assert reg_response.status_code == 200
    assert reg_response.json()["username"] == "testseeker"
    assert reg_response.json()["profile"]["deity_preference"] == "Shiva"

    # Login
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "testseeker", "password": "securepassword"}
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()

def test_scriptures_endpoints():
    # Daily verse
    response = client.get("/api/v1/scriptures/daily-verse")
    assert response.status_code == 200
    assert "sanskrit" in response.json()
    assert "translation" in response.json()

    # Search
    search_response = client.get("/api/v1/scriptures/search?query=karma")
    assert search_response.status_code == 200
    assert search_response.json()["count"] > 0
