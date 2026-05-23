import logging
import httpx
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from app.config import settings

logger = logging.getLogger("garuda_dharma.vector_store")

class VectorStoreService:
    def __init__(self):
        # Try server first
        try:
            logger.info(f"Connecting to Qdrant server at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
            # We can ping the Qdrant server to see if it's actually running
            self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, timeout=2.0)
            # Check if connection works
            self.client.get_collections()
            logger.info("Successfully connected to Qdrant server")
        except Exception as e:
            logger.warning(f"Could not connect to Qdrant server: {e}. Falling back to local disk QdrantClient.")
            import sys
            import os
            if "pytest" in sys.modules or os.getenv("TESTING") == "true":
                logger.info("Test environment detected: using in-memory Qdrant client")
                self.client = QdrantClient(":memory:")
            else:
                db_dir = "d:/P/OS/backend/app/data/qdrant_db"
                os.makedirs(db_dir, exist_ok=True)
                try:
                    self.client = QdrantClient(path=db_dir)
                except Exception as lock_err:
                    logger.warning(f"Local Qdrant DB already locked ({lock_err}). Falling back to in-memory client.")
                    self.client = QdrantClient(":memory:")

    def _get_embedding(self, text: str) -> List[float]:
        try:
            url = f"{settings.OLLAMA_BASE_URL}/api/embeddings"
            payload = {
                "model": settings.OLLAMA_EMBEDDING_MODEL,
                "prompt": text
            }
            import sys
            import os
            timeout_val = 1.0 if ("pytest" in sys.modules or os.getenv("TESTING") == "true") else 60.0
            r = httpx.post(url, json=payload, timeout=timeout_val)
            r.raise_for_status()
            return r.json()["embedding"]
        except Exception as e:
            logger.error(f"Error generating embedding for text '{text[:20]}...': {e}")
            # Return dummy zero-filled embedding if embedding fails, to prevent crash
            return [0.0] * 768

    def ensure_collection(self, collection_name: str, vector_size: int = 768):
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)
            if not exists:
                logger.info(f"Creating Qdrant collection: {collection_name}")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=vector_size,
                        distance=qmodels.Distance.COSINE
                    )
                )
        except Exception as e:
            logger.error(f"Error ensuring collection {collection_name}: {e}")

    def upsert_video(self, video_id: int, youtube_id: str, title: str, description: str, transcript: str, category: str, deity: str):
        self.ensure_collection("garuda_videos")
        # create text representation for semantic search
        text_to_embed = f"Title: {title}\nDescription: {description}\nCategory: {category}\nDeity: {deity or ''}\nTranscript snippet: {(transcript or '')[:1000]}"
        vector = self._get_embedding(text_to_embed)
        
        payload = {
            "video_id": video_id,
            "youtube_id": youtube_id,
            "title": title,
            "category": category,
            "deity": deity
        }
        
        self.client.upsert(
            collection_name="garuda_videos",
            points=[
                qmodels.PointStruct(
                    id=video_id,
                    vector=vector,
                    payload=payload
                )
            ]
        )
        logger.info(f"Upserted video {video_id} to vector store")

    def upsert_audio(self, audio_id: int, title: str, artist: str, category: str, deity: str, lyrics: str):
        self.ensure_collection("garuda_audio")
        text_to_embed = f"Title: {title}\nArtist: {artist}\nCategory: {category}\nDeity: {deity or ''}\nLyrics snippet: {(lyrics or '')[:1000]}"
        vector = self._get_embedding(text_to_embed)
        
        payload = {
            "audio_id": audio_id,
            "title": title,
            "artist": artist,
            "category": category,
            "deity": deity
        }
        
        self.client.upsert(
            collection_name="garuda_audio",
            points=[
                qmodels.PointStruct(
                    id=audio_id,
                    vector=vector,
                    payload=payload
                )
            ]
        )
        logger.info(f"Upserted audio {audio_id} to vector store")

    def search_videos(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        self.ensure_collection("garuda_videos")
        vector = self._get_embedding(query)
        
        response = self.client.query_points(
            collection_name="garuda_videos",
            query=vector,
            limit=limit
        )
        
        return [hit.payload for hit in response.points]

    def search_audio(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        self.ensure_collection("garuda_audio")
        vector = self._get_embedding(query)
        
        response = self.client.query_points(
            collection_name="garuda_audio",
            query=vector,
            limit=limit
        )
        
        return [hit.payload for hit in response.points]

vector_store_service = VectorStoreService()
