import logging
import asyncio
import threading
import time
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.spiritualtube import YoutubeChannel, SpiritualVideo
from app.models.nada import SpiritualAudio
from app.core.youtube_ingestion import youtube_ingestion_service
from app.core.audio_ingestion import audio_ingestion_service
from app.core.crawl_manager import crawl_manager
from app.core.classifier import spiritual_classifier
from app.core.relationship_engine import relationship_engine

logger = logging.getLogger("garuda_dharma.scheduler")

# Background flags
_scheduler_running = False
_scheduler_thread: threading.Thread = None

def run_sync_ingestion():
    """
    Synchronous ingestion wrapper to run inside the background thread.
    """
    logger.info("Scheduler: Starting background sync task...")
    db: Session = SessionLocal()
    try:
        # 1. Run Crawl Queue Processor
        logger.info("Scheduler: Processing crawl queue...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(crawl_manager.trigger_full_crawl())
        except Exception as cqe:
            logger.error(f"Scheduler: Error processing crawl queue: {cqe}")
        finally:
            loop.close()

        # 2. Ingest audio library from Archive.org
        logger.info("Scheduler: Syncing audio library...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(audio_ingestion_service.ingest_audio_library(db, limit=10))
        except Exception as ae:
            logger.error(f"Scheduler: Error syncing audio library: {ae}")
        finally:
            loop.close()
            
        # 3. Discover videos from registered channels
        channels = db.query(YoutubeChannel).filter(YoutubeChannel.is_verified == True).all()
        logger.info(f"Scheduler: Found {len(channels)} verified channels to monitor.")
        for channel in channels:
            logger.info(f"Scheduler: Syncing channel {channel.title} ({channel.channel_id})...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(youtube_ingestion_service.discover_channel_videos(channel.channel_id, db, limit=3))
            except Exception as ce:
                logger.error(f"Scheduler: Error syncing channel {channel.title}: {ce}")
            finally:
                loop.close()
                
            # Sleep a bit between channels to prevent Ollama overloading
            time.sleep(3)
            
        # 4. Process existing pending videos in the database (Ingestion + AI classification + Graph building)
        pending_videos = db.query(SpiritualVideo).filter(SpiritualVideo.moderation_status == "pending").all()
        logger.info(f"Scheduler: Found {len(pending_videos)} pending videos in database to process.")
        for video in pending_videos:
            logger.info(f"Scheduler: Ingesting/Analyzing pending video {video.title} ({video.youtube_id})...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Core Ingest
                ingested_video = loop.run_until_complete(youtube_ingestion_service.ingest_video_by_id(video.youtube_id, db))
                if ingested_video:
                    # Run AI Classifier / Auditor
                    approved = loop.run_until_complete(spiritual_classifier.audit_video(ingested_video, db))
                    if approved:
                        # Build Graph Relationships
                        relationship_engine.build_graph_for_video(ingested_video, db)
            except Exception as ve:
                logger.error(f"Scheduler: Error ingesting/auditing pending video {video.title}: {ve}")
            finally:
                loop.close()
            # Sleep a bit to prevent Ollama overloading
            time.sleep(2)
            
        # 5. Build Graph Relationships for new Audio tracks
        new_audios = db.query(SpiritualAudio).all()
        logger.info(f"Scheduler: Auditing & building relationships for {len(new_audios)} audio tracks...")
        for audio in new_audios:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Audit
                approved = loop.run_until_complete(spiritual_classifier.audit_audio(audio, db))
                if approved:
                    relationship_engine.build_graph_for_audio(audio, db)
            except Exception as aue:
                logger.error(f"Scheduler: Error auditing/building relationships for audio {audio.title}: {aue}")
            finally:
                loop.close()

        logger.info("Scheduler: Background sync task completed successfully.")
    except Exception as e:
        logger.error(f"Scheduler: Error during background sync: {e}")
    finally:
        db.close()


def scheduler_loop(interval_hours: float):
    """
    Infinite loop for the scheduler running in a background thread.
    """
    global _scheduler_running
    logger.info(f"Scheduler: Loop started. Interval set to {interval_hours} hours.")
    
    # Run once immediately on start
    run_sync_ingestion()
    
    while _scheduler_running:
        # Sleep in small increments of 10s so we can shut down quickly if needed
        sleep_target = interval_hours * 3600
        slept = 0
        while slept < sleep_target and _scheduler_running:
            time.sleep(10)
            slept += 10
            
        if _scheduler_running:
            run_sync_ingestion()

def start_scheduler(interval_hours: float = 6.0):
    """
    Starts the background scheduler thread.
    """
    global _scheduler_running, _scheduler_thread
    if _scheduler_running:
        logger.warning("Scheduler: Already running.")
        return
        
    _scheduler_running = True
    _scheduler_thread = threading.Thread(
        target=scheduler_loop,
        args=(interval_hours,),
        daemon=True,
        name="DharmaSchedulerThread"
    )
    _scheduler_thread.start()
    logger.info("Scheduler: Started successfully in background.")

def stop_scheduler():
    """
    Stops the background scheduler thread.
    """
    global _scheduler_running
    if not _scheduler_running:
        return
        
    logger.info("Scheduler: Stopping background loop...")
    _scheduler_running = False
    if _scheduler_thread:
        _scheduler_thread.join(timeout=5)
    logger.info("Scheduler: Stopped.")
