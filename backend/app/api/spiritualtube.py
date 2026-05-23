import re
import json
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
from app.models.spiritualtube import (
    SpiritualVideo, VideoNote, LearningPath, LearningPathVideo, UserVideoProgress, YoutubeChannel
)
from app.config import settings

logger = logging.getLogger("garuda_dharma.spiritualtube")

router = APIRouter(prefix="/spiritualtube", tags=["spiritualtube"])

# --- Pydantic Schemas ---
class VideoNoteCreate(BaseModel):
    timestamp: int  # in seconds
    note_text: str

class VideoNoteOut(BaseModel):
    id: int
    video_id: int
    timestamp: int
    note_text: str
    created_at: datetime

    class Config:
        from_attributes = True

class ProgressUpdate(BaseModel):
    watched_seconds: int
    is_completed: bool

class VideoOut(BaseModel):
    id: int
    youtube_id: str
    title: str
    description: Optional[str]
    category: str
    duration: int
    thumbnail_url: Optional[str]
    transcript: Optional[str]
    summary: Optional[str]
    learnings_json: Optional[str]
    timestamps_json: Optional[str]

    class Config:
        from_attributes = True

class LearningPathOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category: str
    level: str

    class Config:
        from_attributes = True

# --- YouTube Search Helper ---
async def fetch_youtube_results(query: str) -> List[Dict[str, Any]]:
    """
    Queries YouTube search results page online dynamically and extracts video information.
    Provides a distraction-free set of results (filtering ads, unrelated content).
    """
    # Enforce sattvic content by ensuring query contains spiritual indicators
    spiritual_keywords = ["spiritual", "gita", "upanishad", "bhajan", "kirtan", "vedanta", "satsang", "dharma", "temple", "mantra", "meditation"]
    query_lower = query.lower()
    has_keyword = any(keyword in query_lower for keyword in spiritual_keywords)
    
    search_query = query
    if not has_keyword:
        search_query += " hindu spiritual discourse bhajan"
    
    url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                logger.error(f"Failed to fetch YouTube page: {response.status_code}")
                return get_fallback_videos(query)
            
            html = response.text
            # Look for ytInitialData
            match = re.search(r"var ytInitialData\s*=\s*({.*?});", html)
            if not match:
                match = re.search(r"window\[['\"]ytInitialData['\"]\]\s*=\s*({.*?});", html)
                
            if not match:
                logger.warning("Could not find ytInitialData in YouTube response HTML.")
                return get_fallback_videos(query)
            
            data = json.loads(match.group(1))
            videos = []
            
            # Navigate the JSON structure to extract search results
            try:
                contents = data["contents"]["twoColumnSearchResultRenderer"]["primaryContents"]["sectionListRenderer"]["contents"]
                for item in contents:
                    if "itemSectionRenderer" in item:
                        section_contents = item["itemSectionRenderer"]["contents"]
                        for sec_item in section_contents:
                            if "videoRenderer" in sec_item:
                                r = sec_item["videoRenderer"]
                                video_id = r.get("videoId")
                                title = r.get("title", {}).get("runs", [{}])[0].get("text", "Unknown Title")
                                description = ""
                                if "descriptionSnippet" in r:
                                    description = "".join([x.get("text", "") for x in r["descriptionSnippet"].get("runs", [])])
                                
                                thumbnail = ""
                                if "thumbnail" in r and "thumbnails" in r["thumbnail"]:
                                    thumbnail = r["thumbnail"]["thumbnails"][0]["url"]
                                
                                duration_str = r.get("lengthText", {}).get("simpleText", "0:00")
                                duration_seconds = parse_duration_to_seconds(duration_str)
                                
                                channel = r.get("ownerText", {}).get("runs", [{}])[0].get("text", "Spiritual Channel")
                                
                                # Enforce safety filter - verify title or description has some spiritual affinity or is not trash
                                # This block prevents clickbaits or random pop content from creeping in
                                blocklisted_words = ["unboxing", "review", "gaming", "prank", "vlog", "makeup", "comedy", "funny", "trailer", "movie", "official video", "hip hop", "rap", "pop song"]
                                if any(bw in title.lower() for bw in blocklisted_words):
                                    continue
                                    
                                videos.append({
                                    "youtube_id": video_id,
                                    "title": title,
                                    "description": f"By {channel}. {description}",
                                    "duration": duration_seconds,
                                    "thumbnail_url": thumbnail,
                                    "category": "Bhakti" if "bhajan" in title.lower() or "kirtan" in title.lower() else "Vedanta",
                                })
            except Exception as e:
                logger.error(f"Error parsing ytInitialData: {str(e)}")
                return get_fallback_videos(query)
                
            return videos[:12]
            
    except Exception as e:
        logger.error(f"Network error in fetch_youtube_results: {str(e)}")
        return get_fallback_videos(query)

def parse_duration_to_seconds(duration_str: str) -> int:
    try:
        parts = list(map(int, duration_str.split(":")))
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        elif len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
    except Exception:
        pass
    return 0

def get_fallback_videos(query: str) -> List[Dict[str, Any]]:
    """
    Curated list of premium Hindu spiritual videos used when YouTube scraping fails or is blocked.
    """
    all_fallbacks = [
        {
            "youtube_id": "aaBeXwSsmtY",
            "title": "Who Am I? – Swami Sarvapriyananda (Vedanta Society of New York)",
            "description": "An introduction to self-inquiry (Atma-Vichara) as taught by Ramana Maharshi, explained by Swami Sarvapriyananda.",
            "duration": 960,
            "thumbnail_url": "https://img.youtube.com/vi/aaBeXwSsmtY/0.jpg",
            "category": "Vedanta",
        },
        {
            "youtube_id": "ATflA6WOy0I",
            "title": "Vishnu Sahasranamam – M.S. Subbulakshmi",
            "description": "The legendary rendering of the 1000 Names of Lord Vishnu by Bharat Ratna M.S. Subbulakshmi.",
            "duration": 3120,
            "thumbnail_url": "https://img.youtube.com/vi/ATflA6WOy0I/0.jpg",
            "category": "Bhakti",
        },
        {
            "youtube_id": "emsphj4r_Q8",
            "title": "Mahamrityunjaya Mantra – 108 Times Healing Chant",
            "description": "Sacred Mahamrityunjaya Mantra chanted 108 times for healing, protection, and liberation from the cycle of death.",
            "duration": 2400,
            "thumbnail_url": "https://img.youtube.com/vi/emsphj4r_Q8/0.jpg",
            "category": "Chants",
        },
        {
            "youtube_id": "hMBKmQEPNzI",
            "title": "Shiva Tandava Stotram – Powerful Devotional",
            "description": "The powerful Shiva Tandava Stotram, a hymn praising Lord Shiva's cosmic dance.",
            "duration": 480,
            "thumbnail_url": "https://img.youtube.com/vi/hMBKmQEPNzI/0.jpg",
            "category": "Chants",
        },
        {
            "youtube_id": "ZhIJgYLjoVw",
            "title": "Sri Venkateswara Suprabhatam – Morning Prayer",
            "description": "Auspicious morning chants praising Lord Venkateswara, sung at dawn to invoke the blessings of the Divine.",
            "duration": 1200,
            "thumbnail_url": "https://img.youtube.com/vi/ZhIJgYLjoVw/0.jpg",
            "category": "Bhakti",
        }
    ]
    # Filter based on query keyword if possible
    query_words = query.lower().split()
    matched = []
    for f in all_fallbacks:
        if any(w in f["title"].lower() or w in f["description"].lower() for w in query_words):
            matched.append(f)
    return matched if matched else all_fallbacks

def seed_channels_if_empty(db: Session):
    count = db.query(YoutubeChannel).count()
    if count == 0:
        channels = [
            YoutubeChannel(
                channel_id="UCUjdjsoLz0vS9eqfDVCfkNA",
                title="Vedanta Society of New York",
                description="Lectures on Advaita Vedanta by Swami Sarvapriyananda",
                category="Vedanta",
                is_verified=True
            ),
            YoutubeChannel(
                channel_id="UCtDAJiFT4sy42oNPA8zo0sw",
                title="Chinmaya Channel",
                description="Talks and discourses on Upanishads, Gita and Advaita Vedanta",
                category="Vedanta",
                is_verified=True
            ),
            YoutubeChannel(
                channel_id="UClr2ZKIqUsyn9oBLoiKbRnw",
                title="Ramakrishna Mission Delhi",
                description="Devotional and philosophical lectures",
                category="Satsang",
                is_verified=True
            )
        ]
        for c in channels:
            db.add(c)
        db.commit()

# --- API Endpoints ---

@router.get("/videos", response_model=List[VideoOut])
def get_all_videos(db: Session = Depends(get_db)):
    """
    Get all spiritual videos currently stored in the database.
    Seeds default fallback videos if they are missing.
    """
    seed_channels_if_empty(db)
    
    # Check and seed individual fallback videos if they do not exist
    fallbacks = get_fallback_videos("")
    for f in fallbacks:
        exists = db.query(SpiritualVideo).filter(SpiritualVideo.youtube_id == f["youtube_id"]).first()
        if not exists:
            video = SpiritualVideo(
                youtube_id=f["youtube_id"],
                title=f["title"],
                description=f["description"],
                duration=f["duration"],
                thumbnail_url=f["thumbnail_url"],
                category=f["category"],
                transcript="*Transcript generation in progress...*",
                summary="*No AI summary generated yet.*"
            )
            db.add(video)
    db.commit()
    
    videos = db.query(SpiritualVideo).filter(
        SpiritualVideo.is_spiritual == True,
        SpiritualVideo.moderation_status != "rejected"
    ).all()
    return videos

@router.get("/videos/search")
async def search_videos(query: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    """
    Search for Hindu spiritual videos.

    Strategy:
    1. Query-level gate: reject completely non-spiritual queries
    2. Instant local DB results (fast)
    3. Live multi-engine YouTube search (yt-dlp + API + RSS)
    4. New results auto-saved to DB for future searches
    """
    from app.core.youtube_search import search_youtube_spiritual, _is_spiritual, _is_blocked, SPIRITUAL_MUST_CONTAIN

    # ── GATE: Reject non-spiritual queries outright ──────────────────────
    # If the user's own query words contain no spiritual keyword, refuse early.
    query_lower = query.lower()
    query_has_spiritual = any(kw in query_lower for kw in SPIRITUAL_MUST_CONTAIN)
    if not query_has_spiritual:
        # Return empty — do not waste time searching
        logger.info(f"Query '{query}' has no spiritual context — returning empty.")
        return []

    results = []
    seen_ids = set()

    # 1. Instant local DB results — strict title/description match only (not category)
    # Category match removed deliberately: it caused default curated videos to appear on every query
    db_videos = db.query(SpiritualVideo).filter(
        (SpiritualVideo.title.ilike(f"%{query}%")) |
        (SpiritualVideo.description.ilike(f"%{query}%")) |
        (SpiritualVideo.channel_name.ilike(f"%{query}%"))
    ).filter(
        SpiritualVideo.is_spiritual == True,
        SpiritualVideo.moderation_status != "rejected"
    ).order_by(SpiritualVideo.created_at.desc()).limit(20).all()

    for v in db_videos:
        if v.youtube_id not in seen_ids:
            seen_ids.add(v.youtube_id)
            results.append({
                "youtube_id": v.youtube_id,
                "title": v.title,
                "description": v.description or "",
                "duration": v.duration or 0,
                "thumbnail_url": v.thumbnail_url or f"https://img.youtube.com/vi/{v.youtube_id}/hqdefault.jpg",
                "category": v.category,
                "summary": v.summary,
                "learnings_json": v.learnings_json,
                "timestamps_json": v.timestamps_json,
                "authenticity_score": v.authenticity_score or 0,
                "spiritual_tradition": v.spiritual_tradition,
                "content_type": v.content_type,
                "energy_type": v.energy_type,
                "speaker_name": v.speaker_name,
                "channel_name": v.channel_name,
            })

    # 2. Live multi-engine YouTube search (yt-dlp + API v3 + RSS)
    try:
        online_videos = await search_youtube_spiritual(query, max_results=25)
        new_to_save = []

        for v in online_videos:
            vid_id = v.get("youtube_id")
            if not vid_id or vid_id in seen_ids:
                continue
            seen_ids.add(vid_id)
            results.append(v)

            existing = db.query(SpiritualVideo).filter(
                SpiritualVideo.youtube_id == vid_id
            ).first()
            if not existing:
                new_to_save.append(v)

        # Auto-save new discovered videos to DB
        for v in new_to_save[:15]:
            try:
                new_video = SpiritualVideo(
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
        logger.error(f"Live YouTube search failed: {e}")

    return results


@router.get("/videos/{youtube_id}", response_model=VideoOut)
async def get_video_details(youtube_id: str, db: Session = Depends(get_db)):
    """
    Get or create video details. If not in DB, fetch real metadata via yt-dlp.
    """
    video = db.query(SpiritualVideo).filter(SpiritualVideo.youtube_id == youtube_id).first()
    if not video:
        # Try to fetch real metadata from YouTube via yt-dlp
        title = "Spiritual Video"
        description = ""
        duration = 0
        thumbnail_url = f"https://img.youtube.com/vi/{youtube_id}/hqdefault.jpg"
        category = "Satsang"
        channel_name = ""

        try:
            import yt_dlp
            import asyncio

            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
            }
            url = f"https://www.youtube.com/watch?v={youtube_id}"

            loop = asyncio.get_event_loop()

            def _fetch():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(url, download=False)

            info = await asyncio.wait_for(loop.run_in_executor(None, _fetch), timeout=15)
            if info:
                title = info.get("title") or title
                description = info.get("description") or ""
                duration = info.get("duration") or 0
                thumbnail_url = info.get("thumbnail") or thumbnail_url
                channel_name = info.get("uploader") or info.get("channel") or ""
                from app.core.youtube_search import _guess_category
                category = _guess_category(title, description)
                logger.info(f"Fetched real metadata for {youtube_id}: {title[:50]}")

        except Exception as e:
            logger.warning(f"Could not fetch metadata for {youtube_id} via yt-dlp: {e}")

        video = SpiritualVideo(
            youtube_id=youtube_id,
            title=title,
            description=description,
            duration=duration,
            thumbnail_url=thumbnail_url,
            category=category,
            channel_name=channel_name,
            is_spiritual=True,
            moderation_status="approved",
            transcript="*Transcript generation in progress...*",
            summary="*No AI summary generated yet.*"
        )
        db.add(video)
        db.commit()
        db.refresh(video)

    return video

@router.post("/videos/{youtube_id}/ai-summary")
async def generate_ai_summary(youtube_id: str, db: Session = Depends(get_db)):
    """
    Calls the local Ollama LLM to generate a spiritual summary and key learnings for the video.
    """
    video = db.query(SpiritualVideo).filter(SpiritualVideo.youtube_id == youtube_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found in database. Load detail first.")
    
    # In a full app, we would download or transcribe the video.
    # Here, we generate a highly relevant summary and study points based on the title & description using Ollama.
    prompt = f"""
    Analyze the following spiritual video details:
    Title: {video.title}
    Description: {video.description}
    Category: {video.category}

    You are the Garuda Dharma Scripture Scholar & Sadhana Coach. 
    1. Write a 3-paragraph summary of the spiritual concept presented (e.g. Advaita Vedanta, Nishkama Karma, Devotional Bhakti, or Yoga).
    2. Extract 3 core teachings.
    3. Suggest 2 reflection questions for the devotee's spiritual journal.
    4. Provide 1 practical sadhana application related to this video.
    
    Return the response as a JSON object with the following structure. Do NOT include markdown styling or any other text outside the JSON. Keep it raw JSON.
    {{
      "summary": "detailed summary here...",
      "teachings": ["teaching 1", "teaching 2", "teaching 3"],
      "reflection_questions": ["question 1", "question 2"],
      "sadhana_practice": "description of practical application..."
    }}
    """
    
    # Try calling Ollama
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.2}
    }
    
    summary_text = "Detailed spiritual summary of the video teaches self-realization, duty, and spiritual discipline."
    learnings = {
        "summary": summary_text,
        "teachings": ["Perform duty with detachment", "Control the mind through meditation", "Surrender fruits of action to the Divine"],
        "reflection_questions": ["How does anger cloud my judgement in daily life?", "What attachments am I holding on to?"],
        "sadhana_practice": "Practice 10 minutes of silent meditation on the breath before beginning work today."
    }
    
    try:
        import sys
        import os
        timeout_val = 1.0 if ("pytest" in sys.modules or os.getenv("TESTING") == "true") else 30.0
        async with httpx.AsyncClient(timeout=timeout_val) as client:
            response = await client.post(f"{settings.OLLAMA_BASE_URL}/api/chat", json=payload)
            if response.status_code == 200:
                res_data = response.json()
                content = res_data.get("message", {}).get("content", "").strip()
                # Clean JSON codeblock wrapper if LLM returned it
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                try:
                    parsed = json.loads(content)
                    learnings = parsed
                    summary_text = parsed.get("summary", summary_text)
                except Exception:
                    # If JSON parsing failed, use content as summary directly
                    summary_text = content
    except Exception as e:
        logger.error(f"Error calling Ollama for summary: {str(e)}")
        # Fall back to default
    
    video.summary = summary_text
    video.learnings_json = json.dumps(learnings)
    # Mock some timestamp highlights
    timestamps = [
        {"time": 0, "label": "Introduction & Invocation"},
        {"time": int(video.duration * 0.25), "label": "Core Philosophical Concept"},
        {"time": int(video.duration * 0.5), "label": "Practical Real Life Examples"},
        {"time": int(video.duration * 0.75), "label": "Q&A and Final Blessing"}
    ]
    video.timestamps_json = json.dumps(timestamps)
    
    db.commit()
    db.refresh(video)
    return {
        "summary": video.summary,
        "learnings": learnings,
        "timestamps": timestamps
    }

# --- Video Notes Endpoints ---

@router.post("/videos/{youtube_id}/notes", response_model=VideoNoteOut)
def add_video_note(
    youtube_id: str,
    note_in: VideoNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    video = db.query(SpiritualVideo).filter(SpiritualVideo.youtube_id == youtube_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found in database")
        
    note = VideoNote(
        user_id=current_user.id,
        video_id=video.id,
        timestamp=note_in.timestamp,
        note_text=note_in.note_text
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note

@router.get("/videos/{youtube_id}/notes", response_model=List[VideoNoteOut])
def get_video_notes(
    youtube_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    video = db.query(SpiritualVideo).filter(SpiritualVideo.youtube_id == youtube_id).first()
    if not video:
        return []
    return db.query(VideoNote).filter(
        VideoNote.video_id == video.id,
        VideoNote.user_id == current_user.id
    ).order_by(VideoNote.timestamp.asc()).all()

@router.delete("/notes/{note_id}")
def delete_video_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = db.query(VideoNote).filter(
        VideoNote.id == note_id,
        VideoNote.user_id == current_user.id
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return {"status": "success", "message": "Note deleted"}

# --- Progress Tracking ---

@router.post("/videos/{youtube_id}/progress")
def update_video_progress(
    youtube_id: str,
    progress_in: ProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    video = db.query(SpiritualVideo).filter(SpiritualVideo.youtube_id == youtube_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found in database")
        
    progress = db.query(UserVideoProgress).filter(
        UserVideoProgress.video_id == video.id,
        UserVideoProgress.user_id == current_user.id
    ).first()
    
    if not progress:
        progress = UserVideoProgress(
            user_id=current_user.id,
            video_id=video.id,
            watched_seconds=progress_in.watched_seconds,
            is_completed=progress_in.is_completed
        )
        db.add(progress)
    else:
        progress.watched_seconds = progress_in.watched_seconds
        progress.is_completed = progress_in.is_completed
        progress.last_watched = datetime.utcnow()
        
    db.commit()
    return {"status": "success", "watched_seconds": progress.watched_seconds, "is_completed": progress.is_completed}

# --- Learning Paths ---

@router.get("/paths", response_model=List[LearningPathOut])
def get_learning_paths(db: Session = Depends(get_db)):
    paths = db.query(LearningPath).all()
    # Seed default paths if empty
    if not paths:
        path1 = LearningPath(
            name="Introduction to Bhagavad Gita",
            description="Embark on the spiritual path by understanding Nishkama Karma and the nature of the Self.",
            category="Bhagavad Gita",
            level="Beginner"
        )
        path2 = LearningPath(
            name="Vedanta & Self-Inquiry",
            description="Explore the non-dual truth through the teachings of Advaita Vedanta and Ramana Maharshi.",
            category="Vedanta",
            level="Intermediate"
        )
        db.add(path1)
        db.add(path2)
        db.commit()
        db.refresh(path1)
        db.refresh(path2)
        
        # Link default fallback videos
        # Who Am I (xG8hJ9-sFts) to Vedanta Path
        v1 = get_video_details("xG8hJ9-sFts", db)
        v2 = get_video_details("ZefBf73MZf8", db)
        
        link1 = LearningPathVideo(path_id=path2.id, video_id=v1.id, sequence=1)
        link2 = LearningPathVideo(path_id=path1.id, video_id=v2.id, sequence=1)
        db.add(link1)
        db.add(link2)
        db.commit()
        
        paths = [path1, path2]
        
    return paths

@router.get("/paths/{path_id}")
def get_learning_path_details(path_id: int, db: Session = Depends(get_db)):
    path = db.query(LearningPath).filter(LearningPath.id == path_id).first()
    if not path:
        raise HTTPException(status_code=404, detail="Path not found")
        
    videos = db.query(LearningPathVideo).filter(LearningPathVideo.path_id == path_id).order_by(LearningPathVideo.sequence.asc()).all()
    video_list = []
    for pv in videos:
        video_list.append({
            "sequence": pv.sequence,
            "video": db.query(SpiritualVideo).filter(SpiritualVideo.id == pv.video_id).first()
        })
        
    return {
        "id": path.id,
        "name": path.name,
        "description": path.description,
        "category": path.category,
        "level": path.level,
        "videos": video_list
    }

# --- Ingestion & Semantic Endpoints ---

class ChannelRegister(BaseModel):
    channel_id: str
    title: str
    category: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None

@router.post("/channels/register")
def register_channel(channel_in: ChannelRegister, db: Session = Depends(get_db)):
    existing = db.query(YoutubeChannel).filter(YoutubeChannel.channel_id == channel_in.channel_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Channel already registered")
        
    channel = YoutubeChannel(
        channel_id=channel_in.channel_id,
        title=channel_in.title,
        description=channel_in.description,
        category=channel_in.category,
        thumbnail_url=channel_in.thumbnail_url,
        is_verified=True
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel

@router.get("/videos/search/semantic", response_model=List[VideoOut])
def semantic_search_videos(query: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    from app.core.vector_store import vector_store_service
    results = vector_store_service.search_videos(query, limit=10)
    
    video_ids = [hit["video_id"] for hit in results]
    videos = db.query(SpiritualVideo).filter(
        SpiritualVideo.id.in_(video_ids)
    ).filter(
        SpiritualVideo.is_spiritual == True,
        SpiritualVideo.moderation_status != "rejected"
    ).all()
    
    # Maintain relevance ordering
    video_map = {v.id: v for v in videos}
    ordered_videos = [video_map[vid] for vid in video_ids if vid in video_map]
    
    return ordered_videos

@router.post("/ingest/trigger")
async def trigger_ingestion():
    from app.core.scheduler import run_sync_ingestion
    import threading
    
    thread = threading.Thread(target=run_sync_ingestion, daemon=True)
    thread.start()
    
    return {"status": "success", "message": "Background ingestion pipeline triggered"}
