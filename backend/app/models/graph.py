from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class GraphNode(Base):
    __tablename__ = "graph_nodes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    node_type = Column(String, nullable=False) # guru, deity, scripture, concept, tradition, channel, artist
    description = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True) # JSON string for additional attributes
    created_at = Column(DateTime, default=datetime.utcnow)

class GraphRelationship(Base):
    __tablename__ = "graph_relationships"

    id = Column(Integer, primary_key=True, index=True)
    source_node_id = Column(Integer, ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False)
    target_node_id = Column(Integer, ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False)
    relationship_type = Column(String, nullable=False) # teaches, references, collaborates_with, discusses, belongs_to, inspired_by
    weight = Column(Float, default=1.0)
    metadata_json = Column(Text, nullable=True) # JSON string for context
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    source_node = relationship("GraphNode", foreign_keys=[source_node_id])
    target_node = relationship("GraphNode", foreign_keys=[target_node_id])

class CrawlQueue(Base):
    __tablename__ = "crawl_queue"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True, nullable=False)
    source_type = Column(String, nullable=False) # youtube_channel, youtube_playlist, archive_org, sitemap, rss_feed, podcast_feed
    status = Column(String, default="pending") # pending, processing, completed, failed
    depth = Column(Integer, default=0)
    priority = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CrawlHistory(Base):
    __tablename__ = "crawl_history"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    status = Column(String, nullable=False) # success, failed
    bytes_fetched = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0.0)
    discovered_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
