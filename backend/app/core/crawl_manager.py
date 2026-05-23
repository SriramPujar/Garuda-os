import logging
import asyncio
import httpx
import xml.etree.ElementTree as ET
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.graph import CrawlQueue, CrawlHistory
from app.models.spiritualtube import SpiritualVideo, YoutubeChannel
from app.models.nada import SpiritualAudio
from app.core.youtube_ingestion import youtube_ingestion_service, parse_youtube_rss
from app.core.audio_ingestion import audio_ingestion_service

logger = logging.getLogger("garuda_dharma.crawl_manager")

class SpiritualCrawlManager:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.max_depth = 3
        self.max_retries = 3

    async def add_to_queue(self, url: str, source_type: str, db: Session, depth: int = 0, priority: int = 0) -> bool:
        """
        Adds a new URL to the crawl queue if it doesn't already exist.
        """
        if depth > self.max_depth:
            return False
            
        exists = db.query(CrawlQueue).filter(CrawlQueue.url == url).first()
        if exists:
            return False
            
        item = CrawlQueue(
            url=url,
            source_type=source_type,
            status="pending",
            depth=depth,
            priority=priority,
            retry_count=0
        )
        db.add(item)
        try:
            db.commit()
            logger.info(f"Added '{url}' to crawl queue as type '{source_type}'")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding to crawl queue: {e}")
            return False

    async def process_next_queue_item(self, db: Session) -> bool:
        """
        Pulls the highest priority pending item and crawls it.
        """
        item = db.query(CrawlQueue).filter(CrawlQueue.status == "pending").order_by(
            CrawlQueue.priority.desc(),
            CrawlQueue.created_at.asc()
        ).first()

        if not item:
            return False

        logger.info(f"Crawl Manager: Processing queue item: {item.url} (Type: {item.source_type})")
        item.status = "processing"
        db.commit()

        start_time = datetime.utcnow()
        status = "success"
        discovered_count = 0
        bytes_fetched = 0
        error_msg = None

        try:
            if item.source_type == "youtube_channel":
                discovered_count, bytes_fetched = await self._crawl_youtube_channel(item, db)
            elif item.source_type == "youtube_playlist":
                discovered_count, bytes_fetched = await self._crawl_youtube_playlist(item, db)
            elif item.source_type == "archive_org":
                discovered_count, bytes_fetched = await self._crawl_archive_org(item, db)
            elif item.source_type == "rss_feed" or item.source_type == "podcast_feed":
                discovered_count, bytes_fetched = await self._crawl_rss_podcast_feed(item, db)
            elif item.source_type == "sitemap":
                discovered_count, bytes_fetched = await self._crawl_sitemap(item, db)
            else:
                raise ValueError(f"Unknown source type: {item.source_type}")

            item.status = "completed"
        except Exception as e:
            logger.error(f"Error processing crawl queue item {item.url}: {e}", exc_info=True)
            status = "failed"
            error_msg = str(e)
            item.status = "failed"
            item.last_error = error_msg
            item.retry_count += 1
            if item.retry_count < self.max_retries:
                item.status = "pending" # retry later

        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Log to CrawlHistory
        history = CrawlHistory(
            url=item.url,
            source_type=item.source_type,
            status=status,
            bytes_fetched=bytes_fetched,
            duration_seconds=duration,
            discovered_count=discovered_count
        )
        db.add(history)
        db.commit()
        return True

    async def _crawl_youtube_channel(self, item: CrawlQueue, db: Session) -> tuple[int, int]:
        """
        Parses a YouTube channel's RSS feed to discover new videos.
        """
        # Parse channel ID from URL if it's not a direct feed URL
        channel_id = item.url
        if "channel/" in item.url:
            channel_id = item.url.split("channel/")[-1].split("/")[0].split("?")[0]
        elif "youtube.com/feeds/" in item.url:
            match = re.search(r"channel_id=([a-zA-Z0-9_-]+)", item.url)
            if match:
                channel_id = match.group(1)

        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(rss_url, headers=self.headers)
            if r.status_code != 200:
                raise httpx.HTTPStatusError(f"HTTP error {r.status_code} fetching RSS feed", request=r.request, response=r)
            
            xml_content = r.text
            bytes_len = len(xml_content.encode('utf-8'))
            discovered_videos = parse_youtube_rss(xml_content)
            
            new_count = 0
            for v in discovered_videos:
                # Add stub video to DB if not present
                exists = db.query(SpiritualVideo).filter(SpiritualVideo.youtube_id == v["youtube_id"]).first()
                if not exists:
                    video = SpiritualVideo(
                        youtube_id=v["youtube_id"],
                        title=v["title"],
                        description=v["description"],
                        thumbnail_url=v["thumbnail_url"],
                        channel_name=v["channel_name"],
                        category="Vedanta", # default class
                        views=v["views"],
                        moderation_status="pending",
                        is_spiritual=True
                    )
                    db.add(video)
                    new_count += 1
            
            db.commit()
            
            # Seed channel details if not exists
            ch_exists = db.query(YoutubeChannel).filter(YoutubeChannel.channel_id == channel_id).first()
            if not ch_exists and discovered_videos:
                channel = YoutubeChannel(
                    channel_id=channel_id,
                    title=discovered_videos[0]["channel_name"],
                    description="Auto-discovered spiritual channel",
                    category="Satsang",
                    is_verified=True
                )
                db.add(channel)
                db.commit()
                
            return new_count, bytes_len

    async def _crawl_youtube_playlist(self, item: CrawlQueue, db: Session) -> tuple[int, int]:
        """
        Parses a YouTube playlist URL to extract video IDs.
        """
        playlist_id = item.url
        if "list=" in item.url:
            playlist_id = item.url.split("list=")[-1].split("&")[0]

        url = f"https://www.youtube.com/playlist?list={playlist_id}"
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(url, headers=self.headers)
            if r.status_code != 200:
                raise httpx.HTTPStatusError(f"HTTP error {r.status_code} fetching playlist", request=r.request, response=r)
                
            html = r.text
            bytes_len = len(html.encode('utf-8'))
            
            # Simple regex search for video IDs
            video_matches = re.findall(r"\"/watch\?v=([a-zA-Z0-9_-]{11})&amp;list=", html)
            if not video_matches:
                video_matches = re.findall(r"\"videoId\":\"([a-zA-Z0-9_-]{11})\"", html)
                
            video_matches = list(set(video_matches))
            new_count = 0
            for vid in video_matches:
                exists = db.query(SpiritualVideo).filter(SpiritualVideo.youtube_id == vid).first()
                if not exists:
                    video = SpiritualVideo(
                        youtube_id=vid,
                        title=f"Discovered Video {vid}",
                        description="Discovered via playlist crawl",
                        thumbnail_url=f"https://img.youtube.com/vi/{vid}/0.jpg",
                        category="Vedanta",
                        moderation_status="pending",
                        is_spiritual=True
                    )
                    db.add(video)
                    new_count += 1
            db.commit()
            return new_count, bytes_len

    async def _crawl_archive_org(self, item: CrawlQueue, db: Session) -> tuple[int, int]:
        """
        Queries Archive.org and imports tracks.
        """
        # The URL contains query params or search keywords
        # Let's run audio ingestion
        ingested = await audio_ingestion_service.ingest_audio_library(db, limit=15)
        # Note: Archive.org returns count, we mock bytes fetched as approximate search response size
        return ingested, 50000

    async def _crawl_rss_podcast_feed(self, item: CrawlQueue, db: Session) -> tuple[int, int]:
        """
        Parses generic podcast XML RSS feeds to extract audio tracks.
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(item.url, headers=self.headers)
            if r.status_code != 200:
                raise httpx.HTTPStatusError(f"HTTP error {r.status_code} fetching RSS podcast", request=r.request, response=r)
                
            xml_text = r.text
            bytes_len = len(xml_text.encode('utf-8'))
            
            root = ET.fromstring(xml_text)
            new_count = 0
            
            for channel_el in root.findall('./channel'):
                channel_title = channel_el.findtext('title', 'Unknown Podcast')
                
                for item_el in channel_el.findall('./item'):
                    title = item_el.findtext('title')
                    description = item_el.findtext('description', '')
                    enclosure = item_el.find('enclosure')
                    
                    if enclosure is not None:
                        audio_url = enclosure.attrib.get('url')
                        if audio_url and audio_url.endswith('.mp3'):
                            # Deduplicate check
                            exists = db.query(SpiritualAudio).filter(SpiritualAudio.url == audio_url).first()
                            if not exists:
                                # Apply basic spiritual filters
                                spiritual_keywords = ["spiritual", "gita", "upanishad", "bhajan", "kirtan", "vedanta", "satsang", "dharma", "temple", "mantra", "meditation", "sanskrit", "hindu", "veda", "yoga", "advaita"]
                                if not any(k in (title + " " + description).lower() for k in spiritual_keywords):
                                    continue
                                    
                                track = SpiritualAudio(
                                    title=title,
                                    artist=channel_title,
                                    url=audio_url,
                                    category="Chant",
                                    deity="None",
                                    lyrics=description[:1000],
                                    meaning="Discovered via podcast feed",
                                    mood_tags="calm, podcast",
                                    duration=300,
                                    audio_source="podcast_feed"
                                )
                                db.add(track)
                                new_count += 1
                                
            db.commit()
            return new_count, bytes_len

    async def _crawl_sitemap(self, item: CrawlQueue, db: Session) -> tuple[int, int]:
        """
        Parses a temple/ashram sitemap to search for potential video or audio page URLs.
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(item.url, headers=self.headers)
            if r.status_code != 200:
                raise httpx.HTTPStatusError(f"HTTP error {r.status_code} fetching sitemap", request=r.request, response=r)
                
            xml_text = r.text
            bytes_len = len(xml_text.encode('utf-8'))
            
            try:
                root = ET.fromstring(xml_text)
            except Exception:
                # Fallback simple regex parsing for sitemap if namespace issues arise
                urls = re.findall(r"<loc>(.*?)</loc>", xml_text)
                root = None
                
            if root is not None:
                # Find all loc elements
                # Handle potential namespace
                namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                locs = root.findall('.//ns:loc', namespaces)
                if not locs:
                    locs = root.findall('.//loc')
                urls = [loc.text for loc in locs if loc.text]

            new_count = 0
            for u in urls:
                # Filter out irrelevant URLs (assets, styles, etc.)
                if any(ext in u.lower() for ext in [".jpg", ".png", ".css", ".js", ".pdf", "/wp-content/"]):
                    continue
                    
                # Moderation: check if url path indicates spiritual lectures or audio
                spiritual_url_keywords = ["audio", "video", "satsang", "lecture", "bhajan", "kirtan", "chant", "discourse", "gita", "upanishad", "sacred"]
                if any(kw in u.lower() for kw in spiritual_url_keywords):
                    # We can queue this sub-page for potential further indexing or crawler analysis
                    added = await self.add_to_queue(u, "rss_feed" if "feed" in u.lower() else "youtube_playlist", db, depth=item.depth + 1)
                    if added:
                        new_count += 1
                        
            return new_count, bytes_len

    async def trigger_full_crawl(self):
        """
        Runs one cycle of the crawl manager loop.
        """
        db = SessionLocal()
        try:
            logger.info("Triggering background crawler cycle...")
            # Run up to 5 items per cycle
            processed = 0
            while processed < 5:
                success = await self.process_next_queue_item(db)
                if not success:
                    break
                processed += 1
            logger.info(f"Completed crawling cycle: processed {processed} queue items.")
        finally:
            db.close()

crawl_manager = SpiritualCrawlManager()
