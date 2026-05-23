import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.journal import JournalEntry
from app.models.sadhana import SadhanaLog, SadhanaRoutine
from app.models.user import UserProfile

logger = logging.getLogger("garuda_dharma.state_engine")

class SpiritualStateEngine:
    def get_user_profile(self, user_id: int, db: Session) -> UserProfile:
        return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    def evaluate_spiritual_state(self, user_id: int, db: Session) -> Dict[str, Any]:
        """
        Analyzes recent sadhana logs, journal sentiments, and habits to determine user spiritual state.
        States: calm, distracted, spiritually engaged, mentally overloaded, reflective, disciplined, emotionally disturbed.
        """
        logger.info(f"Evaluating spiritual state for user {user_id}")
        
        # 1. Fetch recent journal entry
        recent_journal = db.query(JournalEntry).filter(
            JournalEntry.user_id == user_id
        ).order_by(desc(JournalEntry.created_at)).first()
        
        # Default state weights
        sentiment = 0.0
        dominant_emotion = "neutral"
        reflection_depth = 3
        
        if recent_journal:
            sentiment = recent_journal.sentiment_score
            dominant_emotion = recent_journal.dominant_emotion or "neutral"
            reflection_depth = recent_journal.reflection_depth or 3
            
        # 2. Fetch recent sadhana logs (past 5 logs)
        routines = db.query(SadhanaRoutine).filter(
            SadhanaRoutine.user_id == user_id,
            SadhanaRoutine.is_active == True
        ).all()
        
        routine_ids = [r.id for r in routines]
        
        logs_count = 0
        completed_count = 0
        
        if routine_ids:
            recent_logs = db.query(SadhanaLog).filter(
                SadhanaLog.routine_id.in_(routine_ids)
            ).order_by(desc(SadhanaLog.completed_at)).limit(5).all()
            
            logs_count = len(recent_logs)
            completed_count = sum(1 for log in recent_logs if log.status == "completed")
            
        # Calculate consistency ratio (0 to 1)
        consistency = completed_count / logs_count if logs_count > 0 else 0.5
        
        # 3. Apply state heuristic rules
        state = "reflective"
        explanation = "Steady state of introspection."
        
        # overloaded: high negative sentiment or anxious/stressed emotions
        if dominant_emotion in ["anxious", "stressed", "overloaded", "fear"]:
            state = "mentally overloaded"
            explanation = "Recent reflections indicate feelings of stress and mental strain."
        # emotionally disturbed: angry/sad
        elif dominant_emotion in ["sad", "angry", "disturbed"]:
            state = "emotionally disturbed"
            explanation = "Presence of heavy emotional waves like grief or resentment."
        # disciplined & engaged: high consistency, deep reflections
        elif consistency >= 0.8 and reflection_depth >= 4:
            state = "spiritually engaged"
            explanation = "Strong adherence to daily routines combined with deep contemplative reflection."
        elif consistency >= 0.8:
            state = "disciplined"
            explanation = "Consistent practice of sadhana routines."
        # distracted: low consistency, low reflection depth, neutral sentiment
        elif consistency < 0.4 and reflection_depth <= 2:
            state = "distracted"
            explanation = "Sadhana routines have been skipped frequently, accompanied by lower introspection depth."
        # calm: positive sentiment, stable emotions
        elif sentiment > 0.3 or dominant_emotion in ["peaceful", "calm", "happy"]:
            state = "calm"
            explanation = "Mind feels peaceful, grounded in contentment."
            
        return {
            "state": state,
            "confidence": 0.85,
            "consistency_score": consistency,
            "sentiment_score": sentiment,
            "reflection_depth": reflection_depth,
            "dominant_emotion": dominant_emotion,
            "explanation": explanation
        }

state_engine = SpiritualStateEngine()
