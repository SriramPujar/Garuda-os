import logging
import json
import httpx
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.models.spiritualtube import SpiritualVideo
from app.models.nada import SpiritualAudio

logger = logging.getLogger("garuda_dharma.classifier")

class SpiritualClassifier:
    async def classify_media(self, title: str, description: str, text_content: str) -> Dict[str, Any]:
        """
        Queries Ollama to perform deep spiritual classification and quality scoring.
        """
        snippet = text_content[:4000] if text_content else "No transcript/lyrics available."
        
        prompt = f"""
        You are the Garuda Dharma AI Content Auditor. Analyze the following media details:
        Title: {title}
        Description: {description}
        Snippet: {snippet}
        
        Classify this content and score its authenticity as a genuine Hindu spiritual resource.
        
        Return a JSON object with this exact structure:
        {{
          "spiritual_tradition": "Vaishnavism/Shaivism/Shaktism/Smarta/Advaita/Dvaita/ISKCON/Yoga/None",
          "content_type": "lecture/kirtan/bhajan/mantra/meditation/storytelling/ritual/satsang/philosophy/podcast/None",
          "energy_type": "calming/devotional/energetic/meditative/intellectual",
          "authenticity_score": 85,
          "speaker_name": "Speaker Name or None",
          "scriptures_referenced": ["Gita", "Upanishad", etc.]
        }}
        
        Rules:
        - "authenticity_score" must be an integer from 1 to 100. Lower scores (< 40) for clickbait, politics, commercials, non-spiritual contents, pop songs, sensationalism.
        - "spiritual_tradition" must be one of the listed values. If it has no connection to Hindu spiritual tradition, put "None".
        - Return ONLY raw valid JSON. Do not include markdown codeblocks or extra conversational text.
        """
        
        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                r = await client.post(f"{settings.OLLAMA_BASE_URL}/api/generate", json=payload)
                r.raise_for_status()
                res = r.json()
                data = json.loads(res["response"])
                return data
        except Exception as e:
            logger.error(f"Error calling Ollama classifier: {e}")
            # Safe offline fallback
            return {
                "spiritual_tradition": "Advaita" if "advaita" in (title + " " + description).lower() else "Smarta",
                "content_type": "satsang" if "satsang" in (title + " " + description).lower() else "lecture",
                "energy_type": "intellectual",
                "authenticity_score": 60,
                "speaker_name": "None",
                "scriptures_referenced": []
            }

    async def audit_video(self, video: SpiritualVideo, db: Session) -> bool:
        """
        Classifies and scores a video. Updates fields in SQLite and returns True if approved, False if rejected.
        """
        logger.info(f"Classifier: Auditing video: {video.title}")
        classification = await self.classify_media(
            title=video.title,
            description=video.description or "",
            text_content=video.transcript or ""
        )
        
        video.spiritual_tradition = classification.get("spiritual_tradition", "Smarta")
        video.content_type = classification.get("content_type", "lecture")
        video.energy_type = classification.get("energy_type", "intellectual")
        video.authenticity_score = int(classification.get("authenticity_score", 50))
        video.speaker_name = classification.get("speaker_name", "None")
        
        refs = classification.get("scriptures_referenced", [])
        if isinstance(refs, list):
            video.scriptures_referenced = ",".join(refs)
            
        # Quality filter
        if video.authenticity_score < 40 or video.spiritual_tradition == "None" or video.content_type == "None":
            video.is_spiritual = False
            video.moderation_status = "rejected"
            logger.warning(f"Classifier: Rejected video '{video.title}' with score {video.authenticity_score}")
            approved = False
        else:
            video.is_spiritual = True
            video.moderation_status = "approved"
            logger.info(f"Classifier: Approved video '{video.title}' with score {video.authenticity_score}")
            approved = True
            
        db.commit()
        return approved

    async def audit_audio(self, audio: SpiritualAudio, db: Session) -> bool:
        """
        Classifies, scores, and updates an audio track.
        """
        logger.info(f"Classifier: Auditing audio track: {audio.title}")
        classification = await self.classify_media(
            title=audio.title,
            description=audio.meaning or "",
            text_content=audio.lyrics or ""
        )
        
        audio.spiritual_tradition = classification.get("spiritual_tradition", "Smarta")
        audio.authenticity_score = int(classification.get("authenticity_score", 50))
        
        # Audio is default spiritual unless score is very low
        if audio.authenticity_score < 40 or audio.spiritual_tradition == "None":
            db.delete(audio) # Reject audio
            logger.warning(f"Classifier: Deleted audio '{audio.title}' with score {audio.authenticity_score}")
            approved = False
        else:
            logger.info(f"Classifier: Approved audio '{audio.title}' with score {audio.authenticity_score}")
            approved = True
            
        db.commit()
        return approved

spiritual_classifier = SpiritualClassifier()
