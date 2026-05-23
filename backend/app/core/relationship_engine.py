import logging
import json
import re
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from app.models.graph import GraphNode, GraphRelationship
from app.models.spiritualtube import SpiritualVideo, YoutubeChannel
from app.models.nada import SpiritualAudio
from app.config import settings

logger = logging.getLogger("garuda_dharma.relationship_engine")

# Core vocabularies for rule-based node extraction
DEITIES = ["Shiva", "Krishna", "Rama", "Devi", "Ganesha", "Hanuman", "Narayana", "Lakshmi", "Saraswati", "Brahman"]
SCRIPTURES = ["Bhagavad Gita", "Gita", "Upanishad", "Rigveda", "Yajurveda", "Samaveda", "Atharvaveda", "Ramayana", "Mahabharata", "Puranas", "Brahma Sutras"]
CONCEPTS = ["Advaita", "Dvaita", "Vishishtadvaita", "Bhakti", "Karma", "Dharma", "Maya", "Atman", "Moksha", "Sadhana", "Jnana", "Yoga", "Brahma Muhurta", "Meditation"]
TRADITIONS = ["Vaishnavism", "Shaivism", "Shaktism", "Smarta", "Advaita Vedanta", "ISKCON", "Yoga"]

class SpiritualRelationshipEngine:
    def get_or_create_node(self, name: str, node_type: str, db: Session, description: str = "") -> GraphNode:
        """
        Retrieves an existing node by name or creates a new node in the graph.
        """
        # Case insensitive match check, but save standard casing
        name_clean = name.strip()
        node = db.query(GraphNode).filter(GraphNode.name == name_clean).first()
        if not node:
            node = GraphNode(
                name=name_clean,
                node_type=node_type,
                description=description or f"Spiritual {node_type} node representing {name_clean}"
            )
            db.add(node)
            try:
                db.commit()
                db.refresh(node)
                logger.info(f"Graph: Created node '{name_clean}' of type '{node_type}'")
            except Exception as e:
                db.rollback()
                # Re-query in case of concurrency race condition
                node = db.query(GraphNode).filter(GraphNode.name == name_clean).first()
        return node

    def add_relationship(self, source_name: str, source_type: str, target_name: str, target_type: str, 
                         rel_type: str, db: Session, weight: float = 1.0) -> Optional[GraphRelationship]:
        """
        Creates a directed relationship between two nodes.
        """
        source_node = self.get_or_create_node(source_name, source_type, db)
        target_node = self.get_or_create_node(target_name, target_type, db)

        if not source_node or not target_node:
            return None

        # Check duplicate relationship
        exists = db.query(GraphRelationship).filter(
            GraphRelationship.source_node_id == source_node.id,
            GraphRelationship.target_node_id == target_node.id,
            GraphRelationship.relationship_type == rel_type
        ).first()

        if not exists:
            rel = GraphRelationship(
                source_node_id=source_node.id,
                target_node_id=target_node.id,
                relationship_type=rel_type,
                weight=weight
            )
            db.add(rel)
            try:
                db.commit()
                db.refresh(rel)
                logger.info(f"Graph: Connected '{source_name}' -[{rel_type}]-> '{target_name}'")
                return rel
            except Exception as e:
                db.rollback()
                return None
        return exists

    def build_graph_for_video(self, video: SpiritualVideo, db: Session):
        """
        Extracts spiritual concepts from video title, description, and transcripts,
        then populates the graph database.
        """
        logger.info(f"Graph Engine: Building relationships for video '{video.title}'")
        
        # 1. Create node for the video/channel
        channel_node = self.get_or_create_node(video.channel_name or "Unknown Channel", "channel", db)
        video_node = self.get_or_create_node(video.title, "video", db, description=video.description)
        
        # Connect channel -> video
        self.add_relationship(video.channel_name or "Unknown Channel", "channel", video.title, "video", "references", db)

        text_pool = (video.title + " " + (video.description or "") + " " + (video.transcript or "")).lower()

        # Rule-based extractors
        # 2. Extract Deities
        for deity in DEITIES:
            if deity.lower() in text_pool:
                self.add_relationship(video.title, "video", deity, "deity", "discusses", db)
                
        # 3. Extract Scriptures
        for scripture in SCRIPTURES:
            if scripture.lower() in text_pool:
                self.add_relationship(video.title, "video", scripture, "scripture", "references", db)
                
        # 4. Extract Concepts
        for concept in CONCEPTS:
            if concept.lower() in text_pool:
                self.add_relationship(video.title, "video", concept, "concept", "discusses", db)
                
        # 5. Extract Traditions
        for tradition in TRADITIONS:
            if tradition.lower() in text_pool:
                self.add_relationship(video.title, "video", tradition, "tradition", "belongs_to", db)

        # 6. Extract Speaker mentions
        # E.g. "Swami Sarvapriyananda", "Swami Vivekananda", "Sadhguru", "Sri Sri Ravi Shankar", etc.
        speaker_matches = re.findall(r"(swami\s+[a-zA-Z]+ananda|ramana\s+maharshi|srila\s+prabhupada|mahatma\s+gandhi|swami\s+chinmayananda)", text_pool)
        for sm in speaker_matches:
            speaker_name = sm.title()
            self.add_relationship(speaker_name, "guru", video.title, "video", "teaches", db)
            
        # Recursive Discovery Integration:
        # Check descriptions or comments for external channel links or related video links
        desc_links = re.findall(r"youtube\.com/channel/([a-zA-Z0-9_-]+)", video.description or "")
        desc_links.extend(re.findall(r"youtube\.com/c/([a-zA-Z0-9_-]+)", video.description or ""))
        
        if desc_links:
            from app.core.crawl_manager import crawl_manager
            for ch_id in list(set(desc_links)):
                # Connection / collaboration link found! Queue it for crawling.
                asyncio.create_task(crawl_manager.add_to_queue(
                    url=ch_id,
                    source_type="youtube_channel",
                    db=db,
                    depth=1,
                    priority=2
                ))
                # Add collaboration relationship in graph
                self.add_relationship(video.channel_name or "Unknown Channel", "channel", ch_id, "channel", "collaborates_with", db)

    def build_graph_for_audio(self, audio: SpiritualAudio, db: Session):
        """
        Builds relationships for audio tracks (Nada).
        """
        logger.info(f"Graph Engine: Building relationships for audio track '{audio.title}'")
        
        artist_node = self.get_or_create_node(audio.artist, "artist", db)
        audio_node = self.get_or_create_node(audio.title, "audio", db)
        
        self.add_relationship(audio.artist, "artist", audio.title, "audio", "references", db)

        text_pool = (audio.title + " " + (audio.lyrics or "") + " " + (audio.meaning or "")).lower()

        # Connect Deity
        if audio.deity and audio.deity != "None":
            self.add_relationship(audio.title, "audio", audio.deity, "deity", "discusses", db)
            # Deity belongs to Tradition
            if audio.deity in ["Shiva"]:
                self.add_relationship(audio.deity, "deity", "Shaivism", "tradition", "belongs_to", db)
            elif audio.deity in ["Krishna", "Rama", "Narayana", "Lakshmi"]:
                self.add_relationship(audio.deity, "deity", "Vaishnavism", "tradition", "belongs_to", db)
            elif audio.deity in ["Devi", "Saraswati"]:
                self.add_relationship(audio.deity, "deity", "Shaktism", "tradition", "belongs_to", db)

        # Connect Categories & Concepts
        if audio.category:
            self.add_relationship(audio.title, "audio", audio.category, "concept", "belongs_to", db)

        for concept in CONCEPTS:
            if concept.lower() in text_pool:
                self.add_relationship(audio.title, "audio", concept, "concept", "discusses", db)

relationship_engine = SpiritualRelationshipEngine()
