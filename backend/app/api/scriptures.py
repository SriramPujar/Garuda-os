from fastapi import APIRouter, Query
from typing import List, Dict, Any
import random

from app.core.retrieval import scripture_retrieval_service, SCRIPTURE_DB

router = APIRouter(prefix="/scriptures", tags=["scriptures"])

@router.get("/search")
async def search_scriptures(query: str = Query(..., min_length=2)):
    results = await scripture_retrieval_service.search_scriptures(query)
    return {
        "query": query,
        "count": len(results),
        "results": results
    }

@router.get("/daily-verse")
def get_daily_verse():
    """
    Returns a random verse from our seed scripture database for focus and intention setting.
    """
    verse = random.choice(SCRIPTURE_DB)
    return verse
