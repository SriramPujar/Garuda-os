import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.memory import SpiritualMemory

logger = logging.getLogger("garuda_dharma.memory")

class MemoryManager:
    def save_memory(
        self, 
        user_id: int, 
        memory_type: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None,
        db: Session = None
    ) -> SpiritualMemory:
        """
        Persists a memory block in the SQL database.
        """
        logger.info(f"Saving memory for user {user_id} of type {memory_type}")
        meta_str = json.dumps(metadata or {})
        
        db_memory = SpiritualMemory(
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            metadata_json=meta_str
        )
        db.add(db_memory)
        db.commit()
        db.refresh(db_memory)
        return db_memory

    def recall_memories(
        self,
        user_id: int,
        query: str,
        db: Session,
        limit: int = 3
    ) -> List[SpiritualMemory]:
        """
        Retrieves matching memories using keyword overlap inside content and tags.
        """
        logger.info(f"Recalling memories for query: {query}")
        
        # Pull all memories for the user
        all_memories = db.query(SpiritualMemory).filter(
            SpiritualMemory.user_id == user_id
        ).all()
        
        words = query.lower().split()
        matches = []
        
        for mem in all_memories:
            score = 0
            content_lower = mem.content.lower()
            meta_lower = mem.metadata_json.lower()
            
            for word in words:
                if len(word) > 2:
                    if word in content_lower:
                        score += 2
                    if word in meta_lower:
                        score += 1
            
            if score > 0:
                matches.append((score, mem))
                
        # Sort by score descending
        matches.sort(key=lambda x: x[0], reverse=True)
        return [m[1] for m in matches[:limit]]

    def get_profile_summary(self, user_id: int, db: Session) -> Dict[str, Any]:
        """
        Summarizes the spiritual state and preferences stored in memory.
        """
        memories = db.query(SpiritualMemory).filter(
            SpiritualMemory.user_id == user_id,
            SpiritualMemory.memory_type == "identity"
        ).all()
        
        summary = {
            "goals": [],
            "preferred_deities": [],
            "practices": []
        }
        for mem in memories:
            try:
                meta = json.loads(mem.metadata_json)
                if "goal" in meta:
                    summary["goals"].append(meta["goal"])
                if "deity" in meta:
                    summary["preferred_deities"].append(meta["deity"])
            except Exception:
                pass
        return summary

memory_manager = MemoryManager()
