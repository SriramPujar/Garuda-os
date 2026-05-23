import logging
from typing import List, Dict, Any
from app.config import settings

logger = logging.getLogger("garuda_dharma.retrieval")

# Pre-populated key scriptural dataset for out-of-the-box local operation
SCRIPTURE_DB: List[Dict[str, Any]] = [
    {
        "scripture": "Bhagavad Gita",
        "chapter": 2,
        "verse": "2.47",
        "sanskrit": "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन । मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि ॥",
        "translation": "You have a right to perform your prescribed duty, but you are not entitled to the fruits of action. Never consider yourself the cause of the results of your activities, and never be attached to not doing your duty.",
        "commentary": "Nishkama Karma. Focus on the action itself, not the anxiety of future outcomes. This brings ultimate peace and mental clarity.",
        "theme": "duty, work, anxiety, detachment",
        "deity": "Krishna"
    },
    {
        "scripture": "Bhagavad Gita",
        "chapter": 2,
        "verse": "2.63",
        "sanskrit": "क्रोधाद्भवति सम्मोहः सम्मोहात्स्मृतिविभ्रमः । स्मृतिभ्रंशाद् बुद्धिनाशो बुद्धिनाशात्प्रणश्यति ॥",
        "translation": "From anger arises complete delusion, and from delusion bewilderment of memory. When memory is bewildered, intelligence is lost; and when intelligence is lost, one falls down.",
        "commentary": "Psychological descent of anger: Attachment leads to desire, which leads to anger when blocked. Anger clouds the mind and destroys discrimination.",
        "theme": "anger, mind control, psychology",
        "deity": "Krishna"
    },
    {
        "scripture": "Bhagavad Gita",
        "chapter": 6,
        "verse": "6.5",
        "sanskrit": "उद्धरेदात्मनात्मानं नात्मानमवसादयेत् । आत्मैव ह्यात्मनो बन्धुरात्मैव रिपुरात्मनः ॥",
        "translation": "One must deliver oneself with the help of the mind, and not degrade oneself. The mind is the friend of the conditioned soul, and the enemy as well.",
        "commentary": "Self-reliance. The mind can be your highest ally or your worst opponent. Meditation and discipline train the mind to be a friend.",
        "theme": "mind control, self-reliance, meditation",
        "deity": "Krishna"
    },
    {
        "scripture": "Bhagavad Gita",
        "chapter": 9,
        "verse": "9.22",
        "sanskrit": "अनन्याश्चिन्तयन्तो मां ये जनाः पर्युपासते । तेषां नित्याभियुक्तानां योगक्षेमं वहाम्यहम् ॥",
        "translation": "But those who always worship Me with exclusive devotion, meditating on My transcendental form—to them I carry what they lack, and I preserve what they have.",
        "commentary": "Grace (Yoga-Kshema). Complete surrender to the Divine guarantees spiritual protection and basic sustenance.",
        "theme": "bhakti, devotion, grace, trust",
        "deity": "Krishna"
    },
    {
        "scripture": "Isha Upanishad",
        "chapter": 1,
        "verse": "1.1",
        "sanskrit": "ईशा वास्यमिदं सर्वं यत्किञ्च जगत्यां जगत् । तेन त्यक्तेन भुञ्जीथा मा गृधः कस्यस्विद्धनम् ॥",
        "translation": "All this, whatever moves in this moving world, is enveloped by God. Therefore, find your enjoyment in renunciation; do not covet what belongs to others.",
        "commentary": "Everything belongs to the Supreme. Consume only what is allotted to you with a sense of gratitude, without greed.",
        "theme": "renunciation, ecology, non-attachment",
        "deity": "Brahman"
    },
    {
        "scripture": "Katha Upanishad",
        "chapter": 1,
        "verse": "1.2.2",
        "sanskrit": "श्रेयश्च प्रेयश्च मनुष्यमेतस्तौ सम्परीत्य विविनक्ति धीरः ।",
        "translation": "The good (Shreyas) and the pleasant (Preyas) present themselves to man. The wise man, having examined both, distinguishes one from the other.",
        "commentary": "Wise decision-making. Shreyas is the spiritual path of long-term good, whereas Preyas is the immediate sensory gratification.",
        "theme": "wisdom, choice, discipline",
        "deity": "Yama"
    }
]

class ScriptureRetrievalService:
    def __init__(self):
        # In a real cluster environment, we would initialize QdrantClient here
        self.qdrant_client = None
        self.use_qdrant = False
        
    async def search_scriptures(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves matching scripture documents based on query.
        Falls back to local keyword/theme matching if Qdrant client is not activated.
        """
        logger.info(f"Searching scriptures for: {query}")
        
        words = query.lower().split()
        matches = []
        
        # Simple scoring algorithm based on matching themes, scriptures, or deities
        for doc in SCRIPTURE_DB:
            score = 0
            doc_text = (doc["translation"] + " " + doc["theme"] + " " + doc["commentary"] + " " + doc["sanskrit"]).lower()
            
            for word in words:
                if len(word) > 2:  # Ignore short prepositions
                    if word in doc_text:
                        score += 2
                    if word in doc["theme"].lower():
                        score += 5
                    if word in doc["scripture"].lower():
                        score += 1
            
            if score > 0:
                matches.append((score, doc))
                
        # Sort by score descending
        matches.sort(key=lambda x: x[0], reverse=True)
        results = [m[1] for m in matches[:limit]]
        
        # If no keywords matched, return default verses (e.g. Gita 2.47 and 6.5)
        if not results:
            results = SCRIPTURE_DB[:2]
            
        return results

scripture_retrieval_service = ScriptureRetrievalService()
