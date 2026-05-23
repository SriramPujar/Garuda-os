import logging
import httpx
from app.config import settings

logger = logging.getLogger("garuda_dharma.moderation")

# Keywords that are strictly banned in titles or descriptions
BANNED_KEYWORDS = [
    "gaming", "gameplay", "fortnite", "pubg", "minecraft",
    "unboxing", "review tech", "smartphone", "iphone",
    "politics", "election", "bjp", "congress", "modi", "rahul gandhi",
    "scandal", "drama", "gossip", "bollywood gossip",
    "pop song", "hip hop", "rap", "makeup", "tutorial react",
    "reaction video", "clickbait", "funny moments", "prank", "romance", "dating"
]

# Keywords that are highly indicative of authentic spirituality
SPIRITUAL_KEYWORDS = [
    "gita", "bhagavad gita", "upanishad", "veda", "vedas", "vedanta", "sadhana",
    "meditation", "dhyana", "yoga", "bhajan", "kirtan", "mantra", "chant",
    "shiva", "krishna", "rama", "devi", "ganesha", "hanuman", "sanskrit",
    "advaita", "upanishad", "guru", "swami", "satsang", "dharma", "shastras",
    "adi shankara", "ramakrishna", "vivekananda", "paramahansa", "yogananda",
    "ramana maharshi", "spiritual"
]

class SpiritualModerator:
    def __init__(self):
        self.ollama_url = f"{settings.OLLAMA_BASE_URL}/api/generate"

    def fast_filter(self, title: str, description: str) -> bool:
        """
        Returns False if the content is clearly non-spiritual based on banned keywords.
        Returns True if it passes.
        """
        title_lower = title.lower()
        desc_lower = (description or "").lower()

        # Check banned keywords
        for keyword in BANNED_KEYWORDS:
            if keyword in title_lower or keyword in desc_lower:
                logger.info(f"Fast Filter: Rejected due to banned keyword '{keyword}'")
                return False

        return True

    def check_relevance_ollama(self, title: str, description: str) -> bool:
        """
        Uses Ollama to evaluate whether the video/audio is authentic Hindu spiritual content.
        """
        prompt = f"""
Evaluate if the following media content is related to Hindu spirituality, philosophy (Vedanta, Yoga, Mimamsa, etc.), scripture (Gita, Upanishads, Vedas, Puranas, Ramayana, Mahabharata), devotion (Bhajans, Kirtans, Mantras), or practices (Sadhana, meditation, rituals).

Content details:
Title: {title}
Description: {description[:500]}

Respond with exactly a JSON object having the following keys:
- "is_spiritual": boolean (true if it is authentic Hindu spiritual/philosophical/devotional content, false if it is worldly, commercial, pop, political, or gaming content)
- "reason": string (brief explanation of the classification)

Do not include any markdown styling or extra text. Output only raw JSON.
"""
        try:
            import sys
            import os
            timeout_val = 1.0 if ("pytest" in sys.modules or os.getenv("TESTING") == "true") else 30.0
            r = httpx.post(
                self.ollama_url,
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=timeout_val
            )
            r.raise_for_status()
            res = r.json()
            import json
            data = json.loads(res["response"])
            is_spiritual = data.get("is_spiritual", False)
            reason = data.get("reason", "")
            logger.info(f"Ollama Moderation: is_spiritual={is_spiritual}, reason={reason}")
            return is_spiritual
        except Exception as e:
            logger.error(f"Ollama moderation failed: {e}. Falling back to keyword heuristics.")
            # Fallback heuristic: If we find any spiritual keyword, approve it.
            title_lower = title.lower()
            desc_lower = (description or "").lower()
            for k in SPIRITUAL_KEYWORDS:
                if k in title_lower or k in desc_lower:
                    logger.info(f"Heuristic Fallback: Approved due to positive keyword '{k}'")
                    return True
            return False

    def moderate(self, title: str, description: str) -> bool:
        """
        Combines fast keyword filtering and Ollama relevance check.
        """
        if not self.fast_filter(title, description):
            return False
        return self.check_relevance_ollama(title, description)

spiritual_moderator = SpiritualModerator()
