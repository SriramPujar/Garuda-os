import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.graph import CrawlQueue, CrawlHistory, GraphNode, GraphRelationship
from app.core.crawl_manager import crawl_manager
from app.core.search_engine import search_engine

logger = logging.getLogger("garuda_dharma.discovery_api")

router = APIRouter(prefix="/discovery", tags=["discovery"])

class SeedCreate(BaseModel):
    url: str
    source_type: str # youtube_channel, youtube_playlist, archive_org, sitemap, rss_feed, podcast_feed
    priority: int = 0

@router.get("/search/videos")
async def search_videos(
    query: str,
    tradition: Optional[str] = None,
    energy: Optional[str] = None,
    content_type: Optional[str] = None,
    min_authenticity: int = 0,
    expand: bool = True,
    db: Session = Depends(get_db)
):
    """
    Advanced hybrid search for spiritual videos.
    Combines: DB metadata + Qdrant semantic + multilingual expansion + live YouTube multi-engine.
    STRICT: only Hindu spiritual content is ever returned.
    """
    from app.core.youtube_search import search_youtube_spiritual, _is_spiritual, _is_blocked, SPIRITUAL_MUST_CONTAIN
    from app.models.spiritualtube import SpiritualVideo as SpiritualVideoModel

    # ── GATE: Reject non-spiritual queries outright ──────────────────────
    query_lower = query.lower()
    if not any(kw in query_lower for kw in SPIRITUAL_MUST_CONTAIN):
        logger.info(f"Discovery query '{query}' has no spiritual context — returning empty.")
        return []

    # Step 1: Hybrid local search (Qdrant + SQL + multilingual + graph boosting)
    local_results = await search_engine.hybrid_search_videos(
        db=db,
        query=query,
        tradition=tradition,
        energy=energy,
        content_type=content_type,
        min_authenticity=min_authenticity,
        expand=expand
    )

    # Filter local results too — only keep spiritually verified items
    seen_ids = set()
    results = []
    for r in local_results:
        if _is_spiritual(r.get("title", ""), r.get("description", "")) and not _is_blocked(r.get("title", "")):
            seen_ids.add(r["youtube_id"])
            results.append(r)

    # Step 2: Live YouTube multi-engine search (yt-dlp + API + RSS)
    try:
        online_videos = await search_youtube_spiritual(query, max_results=25)
        new_to_save = []

        for v in online_videos:
            vid_id = v.get("youtube_id")
            if not vid_id or vid_id in seen_ids:
                continue
            seen_ids.add(vid_id)

            # Convert to discovery result format
            results.append({
                "id": None,
                "youtube_id": vid_id,
                "title": v["title"],
                "description": v.get("description", ""),
                "duration": v.get("duration", 0),
                "thumbnail_url": v.get("thumbnail_url", f"https://img.youtube.com/vi/{vid_id}/hqdefault.jpg"),
                "category": v.get("category", "Satsang"),
                "summary": None,
                "learnings_json": None,
                "timestamps_json": None,
                "authenticity_score": 0,
                "spiritual_tradition": None,
                "content_type": None,
                "energy_type": None,
                "speaker_name": None,
                "scriptures_referenced": None,
                "search_score": 0.5,
                "channel_name": v.get("channel_name", ""),
            })

            # Auto-save to DB if not existing
            existing = db.query(SpiritualVideoModel).filter(
                SpiritualVideoModel.youtube_id == vid_id
            ).first()
            if not existing:
                new_to_save.append(v)

        for v in new_to_save[:15]:
            try:
                new_video = SpiritualVideoModel(
                    youtube_id=v["youtube_id"],
                    title=v["title"],
                    description=v.get("description", ""),
                    duration=v.get("duration", 0),
                    thumbnail_url=v.get("thumbnail_url", ""),
                    category=v.get("category", "Satsang"),
                    channel_name=v.get("channel_name", ""),
                    is_spiritual=True,
                    moderation_status="approved",
                    transcript="*Transcript pending...*",
                    summary="*AI summary pending...*",
                )
                db.add(new_video)
            except Exception as save_err:
                logger.warning(f"Could not save video {v['youtube_id']}: {save_err}")

        try:
            db.commit()
        except Exception as commit_err:
            db.rollback()
            logger.warning(f"DB commit failed for new videos: {commit_err}")

    except Exception as e:
        logger.error(f"Live YouTube search in discovery failed: {e}")

    return results



@router.get("/search/audio")
async def search_audio(
    query: str,
    tradition: Optional[str] = None,
    category: Optional[str] = None,
    min_authenticity: int = 0,
    expand: bool = True,
    db: Session = Depends(get_db)
):
    """
    Advanced hybrid search for devotional audio.
    Combines local SQLite, Qdrant semantics, and online Spotify/YouTube Music API.
    """
    from app.core.spotify_search import spotify_search
    from app.models.nada import SpiritualAudio as SpiritualAudioModel
    from app.core.youtube_search import SPIRITUAL_MUST_CONTAIN

    # GATE: Reject non-spiritual queries outright
    query_lower = query.lower()
    if not any(kw in query_lower for kw in SPIRITUAL_MUST_CONTAIN) and not any(kw in query_lower for kw in ["chalisa", "jaap", "stotra", "aarti", "chant", "stotram"]):
        logger.info(f"Discovery audio query '{query}' has no spiritual context — returning empty.")
        return []

    # Step 1: Hybrid local search
    local_results = await search_engine.hybrid_search_audio(
        db=db,
        query=query,
        tradition=tradition,
        category=category,
        min_authenticity=min_authenticity,
        expand=expand
    )

    seen_urls = {r["url"] for r in local_results}
    results = list(local_results)

    # Step 2: Live online Spotify / YouTube fallback search
    try:
        online_tracks = await spotify_search.search_tracks(query, limit=15)
        new_to_save = []

        for t in online_tracks:
            url = t["url"]
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            existing = db.query(SpiritualAudioModel).filter(
                SpiritualAudioModel.url == url
            ).first()
            
            track_id = existing.id if existing else None
            
            # Calculate a query match score for online tracks based on title match
            match_score = 5.0
            title_lower = t["title"].lower()
            query_lower = query.lower()
            if query_lower in title_lower:
                match_score += 10.0
            else:
                for word in query_lower.split():
                    if len(word) > 2 and word in title_lower:
                        match_score += 2.0
            if t["audio_source"] == "spotify" or "spotify.com" in url:
                match_score += 0.5

            # Format to result payload
            results.append({
                "id": track_id,
                "title": t["title"],
                "artist": t["artist"],
                "url": url,
                "category": t["category"],
                "deity": t["deity"],
                "lyrics": t["lyrics"],
                "meaning": t["meaning"],
                "mood_tags": t["mood_tags"],
                "spiritual_intensity": t["spiritual_intensity"],
                "is_mantra_loopable": t["is_mantra_loopable"],
                "duration": t["duration"],
                "audio_source": t["audio_source"],
                "authenticity_score": t["authenticity_score"],
                "spiritual_tradition": tradition,
                "lyrics_translation": None,
                "search_score": round(match_score, 2)
            })

            if not existing:
                new_to_save.append(t)

        for t in new_to_save[:10]:
            try:
                new_audio = SpiritualAudioModel(
                    title=t["title"],
                    artist=t["artist"],
                    url=t["url"],
                    category=t["category"],
                    deity=t["deity"],
                    lyrics=t["lyrics"],
                    meaning=t["meaning"],
                    mood_tags=t["mood_tags"],
                    spiritual_intensity=t["spiritual_intensity"],
                    is_mantra_loopable=t["is_mantra_loopable"],
                    duration=t["duration"],
                    audio_source=t["audio_source"],
                    authenticity_score=t["authenticity_score"],
                    spiritual_tradition=tradition
                )
                db.add(new_audio)
                db.flush() # Assign auto-incrementing ID
                
                # Update ID in results list
                for r in results:
                    if r["url"] == t["url"]:
                        r["id"] = new_audio.id
            except Exception as save_err:
                logger.warning(f"Could not save audio {t['title']}: {save_err}")

        try:
            db.commit()
        except Exception as commit_err:
            db.rollback()
            logger.warning(f"DB commit failed for new audios: {commit_err}")

    except Exception as e:
        logger.error(f"Live Spotify search failed: {e}")

    # Sort final results: primary sort by search_score descending, secondary sort to prefer Spotify
    results.sort(key=lambda x: (-x.get("search_score", 0.0), 0 if (x.get("audio_source") == "spotify" or (x.get("url") and "spotify.com" in x.get("url"))) else 1))

    return results

@router.get("/queue/status")
def get_queue_status(db: Session = Depends(get_db)):
    """
    Gets summary metrics for the crawling queue and crawl history.
    """
    stats = {}
    statuses = ["pending", "processing", "completed", "failed"]
    for s in statuses:
        stats[s] = db.query(CrawlQueue).filter(CrawlQueue.status == s).count()
        
    history = db.query(CrawlHistory).order_by(CrawlHistory.created_at.desc()).limit(15).all()
    history_list = []
    for h in history:
        history_list.append({
            "id": h.id,
            "url": h.url,
            "source_type": h.source_type,
            "status": h.status,
            "bytes_fetched": h.bytes_fetched,
            "duration_seconds": round(h.duration_seconds, 2),
            "discovered_count": h.discovered_count,
            "created_at": h.created_at
        })
        
    return {
        "queue_stats": stats,
        "history": history_list
    }

@router.post("/queue/add")
async def add_seed_url(req: SeedCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Registers a new crawl target URL in the queue.
    """
    added = await crawl_manager.add_to_queue(
        url=req.url,
        source_type=req.source_type,
        db=db,
        priority=req.priority
    )
    if not added:
        raise HTTPException(status_code=400, detail="URL already exists in queue or failed to add.")
    return {"status": "success", "message": f"Successfully queued '{req.url}'"}

@router.post("/queue/trigger")
async def trigger_crawling(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Manually triggers one background crawling cycle.
    """
    # Run async to prevent API timeout
    import asyncio
    asyncio.create_task(crawl_manager.trigger_full_crawl())
    return {"status": "success", "message": "Manual crawler task triggered in background."}

@router.get("/graph")
def get_knowledge_graph(limit: int = 150, db: Session = Depends(get_db)):
    """
    Returns nodes and relationships in the knowledge graph.
    Cap to prevents frontend rendering overload.
    """
    # Fetch core nodes (non-media nodes like gurus, deities, scriptures, traditions, concepts)
    core_nodes = db.query(GraphNode).filter(GraphNode.node_type.notin_(["video", "audio"])).all()
    
    # Fetch recent media nodes to show connection to new items
    media_nodes = db.query(GraphNode).filter(GraphNode.node_type.in_(["video", "audio"])).order_by(GraphNode.created_at.desc()).limit(limit - len(core_nodes)).all()
    
    all_nodes = list(core_nodes) + list(media_nodes)
    node_ids = {n.id for n in all_nodes}
    
    nodes_payload = []
    for n in all_nodes:
        nodes_payload.append({
            "id": str(n.id),
            "name": n.name,
            "type": n.node_type,
            "description": n.description or ""
        })
        
    # Fetch relationships connecting these nodes
    rels = db.query(GraphRelationship).filter(
        GraphRelationship.source_node_id.in_(node_ids),
        GraphRelationship.target_node_id.in_(node_ids)
    ).all()
    
    links_payload = []
    for r in rels:
        links_payload.append({
            "source": str(r.source_node_id),
            "target": str(r.target_node_id),
            "type": r.relationship_type,
            "weight": r.weight
        })
        
    return {
        "nodes": nodes_payload,
        "links": links_payload
    }
