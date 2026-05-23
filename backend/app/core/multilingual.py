import logging
import httpx
from typing import List, Dict, Any
from app.config import settings

logger = logging.getLogger("garuda_dharma.multilingual")

# Static dictionary mapping core terms for rapid indic lookup
INDIC_DICTIONARY: Dict[str, Dict[str, str]] = {
    "krishna": {
        "Sanskrit": "कृष्ण",
        "Hindi": "कृष्णा",
        "Tamil": "கிருஷ்ணர்",
        "Telugu": "కృష్ణుడు",
        "Kannada": "ಕೃಷ್ಣ",
        "Malayalam": "കൃഷ്ണൻ",
        "Bengali": "কৃষ্ণ",
        "Marathi": "कृष्ण",
        "Gujarati": "કૃષ્ણ",
        "Nepali": "कृष्ण"
    },
    "shiva": {
        "Sanskrit": "शिव",
        "Hindi": "शिव",
        "Tamil": "சிவன்",
        "Telugu": "శివుడు",
        "Kannada": "ಶಿವ",
        "Malayalam": "ശിവൻ",
        "Bengali": "শিব",
        "Marathi": "शिव",
        "Gujarati": "શિવ",
        "Nepali": "शिव"
    },
    "devi": {
        "Sanskrit": "देवी",
        "Hindi": "देवी",
        "Tamil": "தேவி",
        "Telugu": "దేవి",
        "Kannada": "ದೇವಿ",
        "Malayalam": "ദേവി",
        "Bengali": "দেবী",
        "Marathi": "देवी",
        "Gujarati": "દેવી",
        "Nepali": "देवी"
    },
    "ganesha": {
        "Sanskrit": "गणेश",
        "Hindi": "गणेश",
        "Tamil": "கணேசர்",
        "Telugu": "గణेशుడు",
        "Kannada": "ಗಣೇಶ",
        "Malayalam": "ഗണേശൻ",
        "Bengali": "গণেশ",
        "Marathi": "गणेश",
        "Gujarati": "ગણેશ",
        "Nepali": "गणेश"
    },
    "rama": {
        "Sanskrit": "राम",
        "Hindi": "राम",
        "Tamil": "ராமர்",
        "Telugu": "రాముడు",
        "Kannada": "ರಾಮ",
        "Malayalam": "രാമൻ",
        "Bengali": "রাম",
        "Marathi": "राम",
        "Gujarati": "રામ",
        "Nepali": "राम"
    },
    "bhajan": {
        "Sanskrit": "भजनम्",
        "Hindi": "भजन",
        "Tamil": "பஜனை",
        "Telugu": "భజన",
        "Kannada": "ಭಜನೆ",
        "Malayalam": "ഭജൻ",
        "Bengali": "ভজন",
        "Marathi": "भजन",
        "Gujarati": "ભજન",
        "Nepali": "भजन"
    },
    "kirtan": {
        "Sanskrit": "कीर्तनम्",
        "Hindi": "कीर्तन",
        "Tamil": "கீர்த்தனை",
        "Telugu": "కీర్తన",
        "Kannada": "ಕೀರ್ತನೆ",
        "Malayalam": "കീർത്തനം",
        "Bengali": "কীর্তন",
        "Marathi": "कीर्तन",
        "Gujarati": "કીર્તન",
        "Nepali": "कीर्तन"
    },
    "mantra": {
        "Sanskrit": "मन्त्र",
        "Hindi": "मंत्र",
        "Tamil": "மந்திரம்",
        "Telugu": "మంత్రము",
        "Kannada": "ಮಂತ್ರ",
        "Malayalam": "മന്ത്രം",
        "Bengali": "মন্ত্র",
        "Marathi": "मंत्र",
        "Gujarati": "મંત્ર",
        "Nepali": "मन्त्र"
    },
    "vedanta": {
        "Sanskrit": "वेदान्त",
        "Hindi": "वेदांत",
        "Tamil": "வேதாந்தம்",
        "Telugu": "వేదాంతము",
        "Kannada": "ವೇದಾಂತ",
        "Malayalam": "വേദാന്തം",
        "Bengali": "বেদান্ত",
        "Marathi": "वेदांत",
        "Gujarati": "વેદાંત",
        "Nepali": "वेदान्त"
    },
    "satsang": {
        "Sanskrit": "सत्सङ्ग",
        "Hindi": "सत्संग",
        "Tamil": "சத்சங்கம்",
        "Telugu": "సత్సంగము",
        "Kannada": "ಸತ್ಸಂಗ",
        "Malayalam": "സത്സംഗം",
        "Bengali": "সতসঙ্গ",
        "Marathi": "सत्संग",
        "Gujarati": "સત્સંગ",
        "Nepali": "सत्संग"
    },
    "upanishad": {
        "Sanskrit": "उपनिषद्",
        "Hindi": "उपनिषद",
        "Tamil": "உபநிடதம்",
        "Telugu": "ఉపనిషత్తు",
        "Kannada": "ಉಪನಿಷತ್",
        "Malayalam": "ഉപനിഷത്ത്",
        "Bengali": "উপনিষদ",
        "Marathi": "उपनिषद",
        "Gujarati": "ઉપનિષદ",
        "Nepali": "उपनिषद"
    },
    "gita": {
        "Sanskrit": "गीता",
        "Hindi": "गीता",
        "Tamil": "கீதை",
        "Telugu": "గీత",
        "Kannada": "ಗೀತೆ",
        "Malayalam": "ഗീത",
        "Bengali": "গীতা",
        "Marathi": "गीता",
        "Gujarati": "ગીતા",
        "Nepali": "गीता"
    }
}

class MultilingualExpansionService:
    def __init__(self):
        self.languages = [
            "Sanskrit", "Hindi", "Tamil", "Telugu", "Kannada",
            "Malayalam", "Bengali", "Marathi", "Gujarati", "Nepali"
        ]

    def expand_from_dict(self, query: str) -> List[str]:
        """
        Attempts to translate query terms using the static Indic dictionary mapping.
        E.g. "shiva bhajan" -> ["shiva bhajan", "शिव भजन", "சிவன் பஜனை", ...]
        """
        query_lower = query.lower().strip()
        words = query_lower.split()
        
        # Check if words match in our dictionary
        has_dictionary_matches = any(word in INDIC_DICTIONARY for word in words)
        if not has_dictionary_matches:
            return []

        expanded = {}
        for lang in self.languages:
            translated_words = []
            for word in words:
                if word in INDIC_DICTIONARY:
                    translated_words.append(INDIC_DICTIONARY[word][lang])
                else:
                    translated_words.append(word)
            expanded[lang] = " ".join(translated_words)
            
        return list(set(expanded.values()))

    async def translate_query_via_llm(self, query: str) -> List[str]:
        """
        Calls Ollama to translate the query into major Indic languages.
        """
        prompt = f"""
        Translate the Hindu spiritual search query: "{query}" into the following languages:
        Sanskrit, Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi, Gujarati, Nepali.
        
        Return the response as a JSON array of strings containing ONLY the translated terms. 
        Example: ["कृष्ण भजन", "கிருஷ்ண பஜனை", ...]
        Do not include markdown tags, code block qualifiers or other text.
        """
        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(f"{settings.OLLAMA_BASE_URL}/api/generate", json=payload)
                r.raise_for_status()
                res = r.json()
                import json
                translations = json.loads(res["response"])
                if isinstance(translations, list):
                    return [str(t).strip() for t in translations if t]
        except Exception as e:
            logger.error(f"Error in LLM multilingual translation: {e}")
            
        return []

    async def expand_query(self, query: str) -> List[str]:
        """
        Combines dictionary lookup and LLM backup to expand a query into multiple languages.
        """
        results = [query]
        
        # 1. Try static dict expansion
        dict_results = self.expand_from_dict(query)
        if dict_results:
            results.extend(dict_results)
            return list(set(results))
            
        # 2. Fallback to LLM translation
        llm_results = await self.translate_query_via_llm(query)
        if llm_results:
            results.extend(llm_results)
            
        return list(set(results))

multilingual_expansion_service = MultilingualExpansionService()
