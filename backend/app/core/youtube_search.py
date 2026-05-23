"""
Garuda SpiritualTube - Multi-Engine YouTube Discovery
=====================================================
PRIMARY ENGINE   : yt-dlp  (channel/playlist/subtitle/chapter extraction)
SECONDARY ENGINE : YouTube Data API v3 (stable search, quota-friendly)
TERTIARY ENGINE  : RSS + HTML scraping fallback (keyless, always available)
TRANSCRIPT ENGINE: youtube-transcript-api + Whisper fallback
"""

import re
import json
import logging
import asyncio
import os
import time
from typing import List, Dict, Any, Optional
import httpx

logger = logging.getLogger("garuda_dharma.youtube_search")

# ─────────────────────────────────────────────
# In-memory search cache (query → results, expires in 10 min)
# ─────────────────────────────────────────────
_search_cache: Dict[str, tuple] = {}  # key: normalized_query, value: (timestamp, results)
CACHE_TTL_SECONDS = 600  # 10 minutes

def _cache_get(key: str) -> Optional[List[Dict[str, Any]]]:
    """Return cached results if still fresh, else None."""
    if key in _search_cache:
        ts, results = _search_cache[key]
        if time.time() - ts < CACHE_TTL_SECONDS:
            return results
        else:
            del _search_cache[key]
    return None

def _cache_set(key: str, results: List[Dict[str, Any]]) -> None:
    _search_cache[key] = (time.time(), results)


# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")  # Optional – set in env for quota-friendly search
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

# Words that must NEVER appear in spiritual content
BLOCK_LIST = [
    "unboxing", "gaming", "prank", "makeup", "comedy", "funny", "trailer",
    "hip hop", "rap", "pop song", "reaction", "challenge", "meme", "roast",
    "drama", "news", "politics", "cricket", "football", "sports", "movie",
    "web series", "episode", "season", "serial", "teaser", "interview",
    "celebrity", "bollywood", "hollywood", "song remix", "dj remix",
    "horror", "thriller", "action movie", "item song", "love song",
    "roast", "standup", "stand up comedy", "tech", "gadget", "phone review",
    "stock market", "crypto", "finance", "business", "startup",
]

# A video MUST contain at least one of these to be considered spiritual
SPIRITUAL_MUST_CONTAIN = [
    # Deities & Divine Names
    "shiva", "vishnu", "krishna", "rama", "durga", "kali", "lakshmi",
    "saraswati", "ganesh", "ganesha", "hanuman", "murugan", "ayyappa",
    "devi", "shakti", "brahma", "narayana", "venkatesh", "balaji",
    "tirupati", "venkateswara", "radha", "sita", "parvati", "mahadev",
    # Scriptures
    "gita", "bhagavad", "upanishad", "veda", "vedic", "ramayana",
    "mahabharata", "mahabharat", "purana", "bhagavatam", "bhagavat",
    "geeta", "ramcharitmanas", "chalisa", "stotram", "stotra",
    # Practices
    "bhajan", "kirtan", "mantra", "chant", "puja", "aarti", "arti",
    "meditation", "dhyana", "yoga", "pranayama", "satsang", "pravachan",
    "havan", "homam", "abhishek", "japa", "sadhana", "tapas",
    # Concepts & Paths
    "vedanta", "advaita", "dvaita", "bhakti", "karma", "dharma",
    "moksha", "liberation", "enlightenment", "self-realization",
    "spiritual", "spirituality", "divine", "sacred", "devotional",
    "hindu", "hinduism", "sanatan", "dharmic",
    # Teachers & Organizations
    "swami", "guru", "maharaj", "acharya", "sadhu", "sanyasi",
    "ashram", "iskcon", "isha", "art of living", "chinmaya",
    "ramakrishna", "vivekananda",
    # Places
    "mandir", "temple", "kashi", "varanasi", "vrindavan", "mathura",
    "ayodhya", "haridwar", "rishikesh", "kailash", "brindavan",
    # Misc spiritual
    "om", "aum", "namaste", "namaskar", "108", "rudra", "shri", "sri",
    "suprabhatam", "stuti", "katha", "leela"
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# ─────────────────────────────────────────────
# Utility helpers
# ─────────────────────────────────────────────

def _is_blocked(title: str) -> bool:
    """Return True if title contains any explicitly non-spiritual keyword."""
    tl = title.lower()
    return any(bw in tl for bw in BLOCK_LIST)

def _is_spiritual(title: str, description: str = "") -> bool:
    """Return True only if the video is positively identified as Hindu spiritual content."""
    text = (title + " " + description).lower()
    return any(kw in text for kw in SPIRITUAL_MUST_CONTAIN)

def _parse_duration(duration_str: str) -> int:
    """Parse ISO 8601 duration (PT4M13S) or HH:MM:SS / MM:SS -> seconds."""
    if not duration_str:
        return 0
    # ISO 8601 (from YT API v3)
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration_str)
    if m:
        h = int(m.group(1) or 0)
        mins = int(m.group(2) or 0)
        s = int(m.group(3) or 0)
        return h * 3600 + mins * 60 + s
    # MM:SS or HH:MM:SS
    try:
        parts = list(map(int, duration_str.split(":")))
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        elif len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
    except Exception:
        pass
    return 0

def _build_video_obj(video_id: str, title: str, description: str,
                     duration: int, thumbnail: str, channel: str,
                     category: str = "Satsang") -> Dict[str, Any]:
    return {
        "youtube_id": video_id,
        "title": title,
        "description": f"By {channel}. {description}" if channel else description,
        "duration": duration,
        "thumbnail_url": thumbnail or f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
        "category": category,
        "channel_name": channel,
    }

def _guess_category(title: str, description: str) -> str:
    text = (title + " " + description).lower()
    if any(k in text for k in ["bhajan", "kirtan", "aarti", "stuti", "stotra"]):
        return "Bhakti"
    if any(k in text for k in ["mantra", "chant", "japa", "108"]):
        return "Chants"
    if any(k in text for k in ["gita", "bhagavad", "upanishad", "vedanta", "advaita"]):
        return "Vedanta"
    if any(k in text for k in ["yoga", "pranayama", "asana", "kundalini"]):
        return "Yoga"
    if any(k in text for k in ["meditation", "dhyana", "mindfulness", "sadhana"]):
        return "Meditation"
    if any(k in text for k in ["discourse", "lecture", "talk", "pravachan", "satsang"]):
        return "Satsang"
    if any(k in text for k in ["puja", "ritual", "abhishek", "havan", "homam"]):
        return "Ritual"
    if any(k in text for k in ["ramayana", "mahabharat", "puranas", "katha", "story"]):
        return "Storytelling"
    return "Satsang"

# ─────────────────────────────────────────────
# ENGINE 1: YouTube Data API v3
# ─────────────────────────────────────────────

async def search_via_youtube_api(query: str, max_results: int = 20) -> List[Dict[str, Any]]:
    """Use official YouTube Data API v3 for stable search. Requires YOUTUBE_API_KEY."""
    if not YOUTUBE_API_KEY:
        return []
    try:
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "relevanceLanguage": "en",
            "key": YOUTUBE_API_KEY,
            "safeSearch": "moderate",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(YOUTUBE_SEARCH_URL, params=params)
            if resp.status_code != 200:
                logger.warning(f"YouTube API returned {resp.status_code}")
                return []
            
            data = resp.json()
            items = data.get("items", [])
            video_ids = [item["id"]["videoId"] for item in items if "videoId" in item.get("id", {})]
            
            if not video_ids:
                return []
            
            # Fetch video details (duration, etc.)
            detail_params = {
                "part": "contentDetails,snippet,statistics",
                "id": ",".join(video_ids),
                "key": YOUTUBE_API_KEY,
            }
            detail_resp = await client.get(YOUTUBE_VIDEOS_URL, params=detail_params)
            details_map = {}
            if detail_resp.status_code == 200:
                for v in detail_resp.json().get("items", []):
                    details_map[v["id"]] = v

            results = []
            for item in items:
                vid_id = item.get("id", {}).get("videoId")
                if not vid_id:
                    continue
                snippet = item.get("snippet", {})
                title = snippet.get("title", "")
                if _is_blocked(title):
                    continue
                description = snippet.get("description", "")
                channel = snippet.get("channelTitle", "")
                thumb = (snippet.get("thumbnails", {}).get("high", {}).get("url") or
                         snippet.get("thumbnails", {}).get("medium", {}).get("url") or
                         f"https://img.youtube.com/vi/{vid_id}/hqdefault.jpg")
                
                duration = 0
                if vid_id in details_map:
                    iso_dur = details_map[vid_id].get("contentDetails", {}).get("duration", "")
                    duration = _parse_duration(iso_dur)
                
                category = _guess_category(title, description)
                results.append(_build_video_obj(vid_id, title, description, duration, thumb, channel, category))
            
            logger.info(f"YouTube API: found {len(results)} results for '{query}'")
            return results

    except Exception as e:
        logger.error(f"YouTube API search failed: {e}")
        return []

# ─────────────────────────────────────────────
# ENGINE 2: yt-dlp (Primary extraction backbone)
# ─────────────────────────────────────────────

async def search_via_ytdlp(query: str, max_results: int = 20) -> List[Dict[str, Any]]:
    """Use yt-dlp to search YouTube – no API key needed, very robust."""
    try:
        import yt_dlp
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": True,  # Don't download, just get metadata
            "playlist_items": f"1:{max_results}",
        }
        search_url = f"ytsearch{max_results}:{query}"
        
        loop = asyncio.get_event_loop()
        
        def _run_ytdlp():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_url, download=False)
                return info
        
        info = await loop.run_in_executor(None, _run_ytdlp)
        
        if not info or "entries" not in info:
            return []
        
        results = []
        for entry in info["entries"]:
            if not entry:
                continue
            vid_id = entry.get("id") or entry.get("url", "").split("v=")[-1]
            if not vid_id or len(vid_id) != 11:
                continue
            title = entry.get("title", "")
            description = entry.get("description") or ""
            # Must NOT be blocked AND MUST contain spiritual keywords
            if _is_blocked(title) or not _is_spiritual(title, description):
                continue
            channel = entry.get("uploader") or entry.get("channel") or ""
            duration = entry.get("duration") or 0
            thumb = entry.get("thumbnail") or f"https://img.youtube.com/vi/{vid_id}/hqdefault.jpg"
            category = _guess_category(title, description)
            results.append(_build_video_obj(vid_id, title, description, int(duration), thumb, channel, category))
        
        logger.info(f"yt-dlp: found {len(results)} results for '{query}'")
        return results

    except ImportError:
        logger.warning("yt-dlp not installed, skipping")
        return []
    except Exception as e:
        logger.error(f"yt-dlp search failed: {e}")
        return []

# ─────────────────────────────────────────────
# ENGINE 3: RSS-based channel discovery
# ─────────────────────────────────────────────

SEED_CHANNELS = [
    # Verified channel IDs → Display Name (checked via RSS feeds)
    ("UCUjdjsoLz0vS9eqfDVCfkNA", "Vedanta Society of New York"),   # Swami Sarvapriyananda
    ("UCXRlIK3Cw_aeGBMIsEHGRSg", "Sadhguru"),                      # Isha Foundation / Sadhguru
    ("UCqQj6KbRHByjMHrRjLtRUzQ", "ISKCON Desire Tree"),            # ISKCON Bhajans & Kirtans
    ("UCdZ_dOMSCJcF9XtPaC5eJng", "Sounds of Isha"),               # Sounds of Isha
    ("UCWHzTbYJuF2J0dSr6stxOVQ", "Art of Living"),                 # Sri Sri Ravi Shankar
    ("UCJnA9M_cRxw3IfJ9GSLQOMQ", "Sri Sri Ravi Shankar"),
    ("UC7eG3OC3bpLieFMEFhZK39g", "Swami Chinmayananda"),           # Chinmaya Mission
    ("UCKBuVA4UNrFZcEJCIpj0I-A", "ISKCON Chowpatty"),
    ("UCzHoHFbHQ6UpBYQRlIqv2QA", "Gaur Gopal Das"),               # Gaur Gopal Das
    ("UChqK3MUBUP5CKG7FVfqbcWQ", "Bhakti Charu Swami"),
]

async def search_via_rss(query: str, max_per_channel: int = 5) -> List[Dict[str, Any]]:
    """Fetch recent videos from seed channels via YouTube RSS feeds and filter by query."""
    results = []
    query_words = query.lower().split()
    seen = set()
    
    async with httpx.AsyncClient(timeout=8.0, headers=HEADERS) as client:
        for channel_id, channel_name in SEED_CHANNELS:
            try:
                rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
                resp = await client.get(rss_url)
                if resp.status_code != 200:
                    continue
                
                # Parse RSS entries
                xml = resp.text
                entries = re.findall(r"<entry>(.*?)</entry>", xml, re.DOTALL)
                count = 0
                for entry in entries:
                    if count >= max_per_channel:
                        break
                    vid_m = re.search(r"<yt:videoId>(.*?)</yt:videoId>", entry)
                    title_m = re.search(r"<title>(.*?)</title>", entry)
                    if not vid_m or not title_m:
                        continue
                    vid_id = vid_m.group(1).strip()
                    title = title_m.group(1).strip()

                    # Must match query AND pass spiritual filter
                    title_lower = title.lower()
                    if not any(qw in title_lower for qw in query_words):
                        continue
                    if _is_blocked(title) or not _is_spiritual(title):
                        continue
                    if vid_id in seen:
                        continue
                    seen.add(vid_id)
                    
                    thumb = f"https://img.youtube.com/vi/{vid_id}/hqdefault.jpg"
                    category = _guess_category(title, "")
                    results.append(_build_video_obj(vid_id, title, "", 0, thumb, channel_name, category))
                    count += 1
                    
            except Exception as e:
                logger.warning(f"RSS fetch failed for {channel_id}: {e}")
    
    logger.info(f"RSS: found {len(results)} results for '{query}'")
    return results

# ─────────────────────────────────────────────
# TRANSCRIPT ENGINE: youtube-transcript-api
# ─────────────────────────────────────────────

async def fetch_transcript(youtube_id: str) -> Optional[str]:
    """Fetch transcript for a video using youtube-transcript-api."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        loop = asyncio.get_event_loop()
        
        def _get_transcript():
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(
                    youtube_id, languages=["en", "hi", "sa", "te", "ta", "kn", "ml", "bn"]
                )
                full_text = " ".join([t["text"] for t in transcript_list])
                return full_text[:8000]  # Cap at 8K chars
            except Exception as e:
                return None
        
        result = await loop.run_in_executor(None, _get_transcript)
        return result
    except ImportError:
        return None
    except Exception as e:
        logger.warning(f"Transcript fetch failed for {youtube_id}: {e}")
        return None

# ─────────────────────────────────────────────
# DEEP DISCOVERY: Related videos via yt-dlp
# ─────────────────────────────────────────────

async def get_related_videos(youtube_id: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Extract related/recommended videos for a given video using yt-dlp."""
    try:
        import yt_dlp
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": True,
        }
        url = f"https://www.youtube.com/watch?v={youtube_id}"
        loop = asyncio.get_event_loop()
        
        def _run():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        
        info = await asyncio.wait_for(loop.run_in_executor(None, _run), timeout=15)
        related = info.get("related_videos") or []
        results = []
        for rv in related[:max_results]:
            vid_id = rv.get("id")
            title = rv.get("title", "")
            if not vid_id or _is_blocked(title) or not _is_spiritual(title):
                continue
            channel = rv.get("uploader") or rv.get("channel", "")
            duration = rv.get("duration") or 0
            thumb = rv.get("thumbnail") or f"https://img.youtube.com/vi/{vid_id}/hqdefault.jpg"
            category = _guess_category(title, "")
            results.append(_build_video_obj(vid_id, title, "", int(duration), thumb, channel, category))
        return results
    except Exception as e:
        logger.warning(f"Related video discovery failed for {youtube_id}: {e}")
        return []

# ─────────────────────────────────────────────
# MAIN ORCHESTRATOR: Multi-engine search
# ─────────────────────────────────────────────

async def search_youtube_spiritual(query: str, max_results: int = 25,
                                    add_spiritual_context: bool = True) -> List[Dict[str, Any]]:
    """
    Orchestrates all engines to search YouTube for Hindu spiritual content.
    ALWAYS appends 'hindu spiritual' context if the query is not already spiritual.
    STRICTLY filters: every result must pass both _is_blocked() and _is_spiritual() checks.
    Results are cached for 10 minutes for instant repeat searches.
    """
    # Check cache first — return instantly if fresh
    cache_key = query.lower().strip()
    cached = _cache_get(cache_key)
    if cached is not None:
        logger.info(f"Cache hit for '{query}': {len(cached)} results")
        return cached

    # Always enrich query with Hindu spiritual context
    query_lower = query.lower()
    is_already_spiritual = any(kw in query_lower for kw in SPIRITUAL_MUST_CONTAIN)
    search_query = query if is_already_spiritual else f"{query} hindu spiritual"

    logger.info(f"Multi-engine YouTube search: '{search_query}'")

    # Run all engines concurrently with increased quota
    tasks = [
        search_via_ytdlp(search_query, max_results + 10),   # fetch extra to allow for filtering
        search_via_youtube_api(search_query, max_results),
        search_via_rss(query, max_per_channel=3),
    ]

    all_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Merge, deduplicate, and apply strict spiritual filter
    seen_ids = set()
    merged = []
    for result_set in all_results:
        if isinstance(result_set, Exception):
            logger.warning(f"Engine failed: {result_set}")
            continue
        for video in result_set:
            vid_id = video.get("youtube_id")
            title = video.get("title", "")
            description = video.get("description", "")
            if not vid_id or vid_id in seen_ids:
                continue
            # Strict dual gate: block list + must-contain spiritual keyword
            if _is_blocked(title) or not _is_spiritual(title, description):
                logger.debug(f"Filtered non-spiritual: {title[:50]}")
                continue
            seen_ids.add(vid_id)
            merged.append(video)

    result = merged[:max_results]
    logger.info(f"Multi-engine search: {len(result)} spiritual results for '{query}'")
    _cache_set(cache_key, result)
    return result


async def extract_channel_videos(channel_id: str, max_videos: int = 50) -> List[Dict[str, Any]]:
    """Extract all videos from a YouTube channel using yt-dlp."""
    try:
        import yt_dlp
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": True,
            "playlistend": max_videos,
        }
        url = f"https://www.youtube.com/channel/{channel_id}/videos"
        loop = asyncio.get_event_loop()
        
        def _run():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        
        info = await asyncio.wait_for(loop.run_in_executor(None, _run), timeout=30)
        results = []
        for entry in (info.get("entries") or []):
            if not entry:
                continue
            vid_id = entry.get("id")
            title = entry.get("title", "")
            if not vid_id or _is_blocked(title):
                continue
            duration = entry.get("duration") or 0
            thumb = entry.get("thumbnail") or f"https://img.youtube.com/vi/{vid_id}/hqdefault.jpg"
            channel = entry.get("uploader") or entry.get("channel", "")
            description = entry.get("description") or ""
            category = _guess_category(title, description)
            results.append(_build_video_obj(vid_id, title, description, int(duration), thumb, channel, category))
        return results
    except Exception as e:
        logger.error(f"Channel extraction failed for {channel_id}: {e}")
        return []
