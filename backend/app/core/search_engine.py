import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.spiritualtube import SpiritualVideo
from app.models.nada import SpiritualAudio
from app.models.graph import GraphNode, GraphRelationship
from app.core.multilingual import multilingual_expansion_service
from app.core.vector_store import vector_store_service

logger = logging.getLogger("garuda_dharma.search_engine")

class SpiritualSearchEngine:
    async def hybrid_search_videos(self, db: Session, query: str, tradition: Optional[str] = None, 
                                   energy: Optional[str] = None, content_type: Optional[str] = None,
                                   min_authenticity: int = 0, expand: bool = True, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Combines SQL text search, Qdrant vectors, multilingual expansion, and Graph boosting
        to retrieve and rank spiritual videos.
        """
        logger.info(f"Hybrid Search: Searching videos for query '{query}'")
        
        # 1. Expand query into Indic languages if requested
        if expand:
            expanded_queries = await multilingual_expansion_service.expand_query(query)
        else:
            expanded_queries = [query]
        logger.info(f"Hybrid Search: Expanded query into {len(expanded_queries)} terms: {expanded_queries}")

        # 2. Get Semantic hits from Qdrant
        semantic_hits = []
        try:
            # We run semantic search for the primary English query
            semantic_hits = vector_store_service.search_videos(query, limit=limit * 2)
        except Exception as e:
            logger.warning(f"Hybrid Search: Semantic search failed: {e}")

        # Create a dict of semantic scores for boosting
        semantic_scores = {hit["video_id"]: 0.5 for hit in semantic_hits} # default score weight

        # 3. Retrieve matching items from database
        # Build SQL keyword filter — title and description ONLY (not category)
        # Category match excluded: broad values like "Satsang"/"Bhakti" match every spiritual query
        filters = []
        for eq in expanded_queries:
            filters.append(SpiritualVideo.title.ilike(f"%{eq}%"))
            filters.append(SpiritualVideo.description.ilike(f"%{eq}%"))

        video_query = db.query(SpiritualVideo).filter(
            SpiritualVideo.is_spiritual == True,
            SpiritualVideo.moderation_status != "rejected"
        )

        if filters:
            video_query = video_query.filter(or_(*filters))

        # Include semantic hits only if they ALSO pass the keyword filter
        # (avoids always pulling the same 9 heavily-embedded curated videos)
        if semantic_scores and filters:
            semantic_ids = list(semantic_scores.keys())
            video_query = db.query(SpiritualVideo).filter(
                or_(
                    SpiritualVideo.id.in_(semantic_ids),
                    *filters
                )
            ).filter(
                SpiritualVideo.is_spiritual == True,
                SpiritualVideo.moderation_status != "rejected"
            )

        # Apply user filters
        if tradition and tradition != "All":
            video_query = video_query.filter(SpiritualVideo.spiritual_tradition == tradition)
        if energy and energy != "All":
            video_query = video_query.filter(SpiritualVideo.energy_type == energy)
        if content_type and content_type != "All":
            video_query = video_query.filter(SpiritualVideo.content_type == content_type)
        if min_authenticity > 0:
            video_query = video_query.filter(SpiritualVideo.authenticity_score >= min_authenticity)

        videos = video_query.all()

        # 4. Graph Boosting
        # Find if query mentions a Deity/Guru/Scripture node in the graph, and boost related videos
        boosted_titles = set()
        try:
            # Look for graph nodes matching query words
            for eq in expanded_queries:
                matched_nodes = db.query(GraphNode).filter(GraphNode.name.ilike(f"%{eq}%")).all()
                for node in matched_nodes:
                    # Find all targets connected to this node
                    rels = db.query(GraphRelationship).filter(
                        or_(
                            GraphRelationship.source_node_id == node.id,
                            GraphRelationship.target_node_id == node.id
                        )
                    ).all()
                    for r in rels:
                        # Fetch the names of related nodes
                        src = db.query(GraphNode).filter(GraphNode.id == r.source_node_id).first()
                        tgt = db.query(GraphNode).filter(GraphNode.id == r.target_node_id).first()
                        if src and src.node_type == "video":
                            boosted_titles.add(src.name)
                        if tgt and tgt.node_type == "video":
                            boosted_titles.add(tgt.name)
        except Exception as ge:
            logger.warning(f"Hybrid Search: Graph boosting traversal failed: {ge}")

        # 5. Rank and Sort results — require minimum relevance score
        ranked_results = []
        for v in videos:
            score = 0.0
            # Base score from keyword match count (primary signal)
            for eq in expanded_queries:
                if eq.lower() in v.title.lower():
                    score += 2.0  # title match is strong signal
                if v.description and eq.lower() in v.description.lower():
                    score += 0.5

            # Semantic boost only if also keyword matched
            if v.id in semantic_scores and score > 0:
                score += 1.5

            # Graph boost
            if v.title in boosted_titles:
                score += 1.5

            # Authenticity boost
            score += (v.authenticity_score or 50) * 0.02

            # MINIMUM RELEVANCE GATE: must have at least one keyword match
            # This prevents low-relevance curated videos from always appearing
            if score > 1.0:  # requires at least partial title/description match
                ranked_results.append((score, v))

        # Sort by score desc
        ranked_results.sort(key=lambda x: x[0], reverse=True)

        final_list = []
        for score, v in ranked_results[:limit]:
            final_list.append({
                "id": v.id,
                "youtube_id": v.youtube_id,
                "title": v.title,
                "description": v.description or "",
                "duration": v.duration or 0,
                "thumbnail_url": v.thumbnail_url or f"https://img.youtube.com/vi/{v.youtube_id}/hqdefault.jpg",
                "category": v.category,
                "summary": v.summary,
                "learnings_json": v.learnings_json,
                "timestamps_json": v.timestamps_json,
                "authenticity_score": v.authenticity_score or 0,
                "spiritual_tradition": v.spiritual_tradition,
                "content_type": v.content_type,
                "energy_type": v.energy_type,
                "speaker_name": v.speaker_name,
                "scriptures_referenced": v.scriptures_referenced,
                "search_score": round(score, 2)
            })

        return final_list

    async def hybrid_search_audio(self, db: Session, query: str, tradition: Optional[str] = None,
                                  category: Optional[str] = None, min_authenticity: int = 0,
                                  expand: bool = True, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Combines SQL search, Qdrant semantic, multilingual expansion, and Graph boosting
        to retrieve and rank devotional audio tracks.
        """
        logger.info(f"Hybrid Search: Searching audio for query '{query}'")
        
        if expand:
            expanded_queries = await multilingual_expansion_service.expand_query(query)
        else:
            expanded_queries = [query]
        
        semantic_hits = []
        try:
            semantic_hits = vector_store_service.search_audio(query, limit=limit * 2)
        except Exception as e:
            logger.warning(f"Hybrid Search: Semantic audio search failed: {e}")
            
        semantic_scores = {hit["audio_id"]: 0.5 for hit in semantic_hits}
        
        filters = []
        for eq in expanded_queries:
            filters.append(SpiritualAudio.title.ilike(f"%{eq}%"))
            filters.append(SpiritualAudio.artist.ilike(f"%{eq}%"))
            filters.append(SpiritualAudio.lyrics.ilike(f"%{eq}%"))
            
        audio_query = db.query(SpiritualAudio)
        
        if filters:
            audio_query = audio_query.filter(or_(*filters))
            
        if semantic_scores:
            semantic_ids = list(semantic_scores.keys())
            audio_query = db.query(SpiritualAudio).filter(
                or_(
                    SpiritualAudio.id.in_(semantic_ids),
                    *filters
                )
            )

        if tradition and tradition != "All":
            audio_query = audio_query.filter(SpiritualAudio.spiritual_tradition == tradition)
        if category and category != "All":
            audio_query = audio_query.filter(SpiritualAudio.category == category)
        if min_authenticity > 0:
            audio_query = audio_query.filter(SpiritualAudio.authenticity_score >= min_authenticity)

        tracks = audio_query.all()
        
        # Graph boosting
        boosted_titles = set()
        try:
            for eq in expanded_queries:
                matched_nodes = db.query(GraphNode).filter(GraphNode.name.ilike(f"%{eq}%")).all()
                for node in matched_nodes:
                    rels = db.query(GraphRelationship).filter(
                        or_(
                            GraphRelationship.source_node_id == node.id,
                            GraphRelationship.target_node_id == node.id
                        )
                    ).all()
                    for r in rels:
                        src = db.query(GraphNode).filter(GraphNode.id == r.source_node_id).first()
                        tgt = db.query(GraphNode).filter(GraphNode.id == r.target_node_id).first()
                        if src and src.node_type == "audio":
                            boosted_titles.add(src.name)
                        if tgt and tgt.node_type == "audio":
                            boosted_titles.add(tgt.name)
        except Exception as ge:
            logger.warning(f"Hybrid Search: Audio graph boosting failed: {ge}")

        ranked_results = []
        for t in tracks:
            score = 0.0
            for eq in expanded_queries:
                if eq.lower() in t.title.lower():
                    score += 10.0
                if t.artist and eq.lower() in t.artist.lower():
                    score += 3.0
                    
            if t.id in semantic_scores:
                score += 5.0
                
            if t.title in boosted_titles:
                score += 4.0
                
            score += (t.authenticity_score or 50) * 0.02
            
            # Boost Spotify tracks slightly to serve as a tie-breaker
            if t.audio_source == "spotify" or (t.url and "spotify.com" in t.url):
                score += 0.5
                
            ranked_results.append((score, t))
            
        ranked_results.sort(key=lambda x: x[0], reverse=True)
        
        final_list = []
        for score, t in ranked_results[:limit]:
            final_list.append({
                "id": t.id,
                "title": t.title,
                "artist": t.artist,
                "url": t.url,
                "category": t.category,
                "deity": t.deity,
                "lyrics": t.lyrics,
                "meaning": t.meaning,
                "mood_tags": t.mood_tags,
                "spiritual_intensity": t.spiritual_intensity,
                "is_mantra_loopable": t.is_mantra_loopable,
                "duration": t.duration,
                "audio_source": t.audio_source,
                "authenticity_score": t.authenticity_score or 0,
                "spiritual_tradition": t.spiritual_tradition,
                "lyrics_translation": t.lyrics_translation,
                "search_score": round(score, 2)
            })
            
        return final_list

search_engine = SpiritualSearchEngine()
