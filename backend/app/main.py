from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import settings
from app.database import engine, Base
# Import models to ensure they are registered on Base
import app.models as models

# Create database tables automatically
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logging.error(f"Error creating database tables: {str(e)}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

from app.core.scheduler import start_scheduler, stop_scheduler

@app.on_event("startup")
def startup_event():
    start_scheduler(interval_hours=12.0)

@app.on_event("shutdown")
def shutdown_event():
    stop_scheduler()

# Set up CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to localhost / NextJS port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import Routers
from app.api import auth, chat, sadhana, journal, ritual, scriptures, spiritualtube, nada, workspace, discovery

app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)
app.include_router(sadhana.router, prefix=settings.API_V1_STR)
app.include_router(journal.router, prefix=settings.API_V1_STR)
app.include_router(ritual.router, prefix=settings.API_V1_STR)
app.include_router(scriptures.router, prefix=settings.API_V1_STR)
app.include_router(spiritualtube.router, prefix=settings.API_V1_STR)
app.include_router(nada.router, prefix=settings.API_V1_STR)
app.include_router(workspace.router, prefix=settings.API_V1_STR)
app.include_router(discovery.router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "status": "online",
        "system": "Garuda Dharma OS Backend",
        "api_docs": "/docs"
    }
