import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.spiritualtube import SpiritualVideo
from app.models.nada import SpiritualAudio
from app.core.state_engine import state_engine

logger = logging.getLogger("garuda_dharma.recommendation")

class SpiritualRecommendationEngine:
    def recommend_for_user(self, user_id: int, db: Session, limit: int = 4) -> Dict[str, Any]:
        """
        Suggests videos and audio tracks based on the user's active spiritual state,
        consistency score, and emotional balance.
        """
        # Evaluate user state
        state_info = state_engine.evaluate_spiritual_state(user_id, db)
        state = state_info["state"]
        explanation = state_info["explanation"]
        
        logger.info(f"Recommending content for user {user_id} based on state '{state}'")
        
        videos_query = db.query(SpiritualVideo).filter(SpiritualVideo.is_spiritual == True, SpiritualVideo.moderation_status == "approved")
        audio_query = db.query(SpiritualAudio)
        
        # Filter content matches according to the spiritual state
        if state == "mentally overloaded":
            # Focus on extreme calming, relaxation, breathing and basic chants
            videos = videos_query.filter(
                (SpiritualVideo.category.in_(["Chants", "Yoga"])) |
                (SpiritualVideo.title.like("%peace%")) |
                (SpiritualVideo.title.like("%mind%")) |
                (SpiritualVideo.title.like("%calm%")) |
                (SpiritualVideo.title.like("%anxiety%"))
            ).limit(limit).all()
            
            tracks = audio_query.filter(
                (SpiritualAudio.category.in_(["Mantra", "Meditation"])) |
                (SpiritualAudio.mood_tags.like("%calm%"))
            ).limit(limit).all()
            
        elif state == "emotionally disturbed":
            # Devotional bhakti content, surrender (Prapatti), bhajans to soothe emotional waves
            videos = videos_query.filter(
                (SpiritualVideo.category.in_(["Bhakti", "Satsang"])) |
                (SpiritualVideo.title.like("%surrender%")) |
                (SpiritualVideo.title.like("%love%")) |
                (SpiritualVideo.title.like("%grief%")) |
                (SpiritualVideo.title.like("%anger%"))
            ).limit(limit).all()
            
            tracks = audio_query.filter(
                (SpiritualAudio.category.in_(["Bhajan", "Kirtan"])) |
                (SpiritualAudio.mood_tags.like("%bhakti%"))
            ).limit(limit).all()
            
        elif state == "distracted":
            # High intensity, motivational, self-mastery, focus on duty (Gita) and mind control
            videos = videos_query.filter(
                (SpiritualVideo.category.in_(["Bhagavad Gita", "Vedanta"])) |
                (SpiritualVideo.title.like("%discipline%")) |
                (SpiritualVideo.title.like("%focus%")) |
                (SpiritualVideo.title.like("%action%")) |
                (SpiritualVideo.title.like("%karma%"))
            ).limit(limit).all()
            
            tracks = audio_query.filter(
                (SpiritualAudio.category.in_(["Chant", "Mantra"])) |
                (SpiritualAudio.mood_tags.like("%focus%"))
            ).limit(limit).all()
            
        else: # calm, reflective, spiritually engaged, disciplined
            # Advanced Vedanta, deep Upanishadic philosophy, scripture commentary
            videos = videos_query.filter(
                SpiritualVideo.category.in_(["Vedanta", "Bhagavad Gita", "Upanishads"])
            ).limit(limit).all()
            
            tracks = audio_query.filter(
                SpiritualAudio.category.in_(["Chant", "Meditation", "Temple Recording"])
            ).limit(limit).all()
            
        # Fallbacks if state-based filtering returned empty results (e.g. clean db)
        if not videos:
            videos = videos_query.limit(limit).all()
        if not tracks:
            tracks = audio_query.limit(limit).all()
            
        return {
            "state": state,
            "explanation": explanation,
            "confidence": state_info["confidence"],
            "recommended_videos": videos,
            "recommended_tracks": tracks
        }

recommendation_engine = SpiritualRecommendationEngine()
