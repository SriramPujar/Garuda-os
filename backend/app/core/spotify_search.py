import os
import base64
import httpx
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("garuda_dharma.spotify_search")

class SpotifySearchService:
    def __init__(self):
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID") or os.getenv("spotify_client_id")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET") or os.getenv("spotify_client_secret")
        self.access_token = None

    async def _get_access_token(self) -> bool:
        # Re-fetch from environment just in case they were set at runtime
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID") or os.getenv("spotify_client_id")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET") or os.getenv("spotify_client_secret")
        
        if not self.client_id or not self.client_secret:
            return False
        
        if self.access_token:
            return True
            
        url = "https://accounts.spotify.com/api/token"
        
        # Base64 encode client_id:client_secret for Spotify client credentials auth
        client_creds = f"{self.client_id}:{self.client_secret}"
        b64_creds = base64.b64encode(client_creds.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {b64_creds}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "client_credentials"
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, data=data)
                if response.status_code == 200:
                    res_data = response.json()
                    self.access_token = res_data.get("access_token")
                    logger.info("Successfully authenticated with Spotify Client Credentials Flow.")
                    return True
                else:
                    logger.error(f"Spotify token request failed: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Error fetching Spotify access token: {e}")
        return False

    async def search_tracks(self, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        # Enforce Hindu spiritual context
        spiritual_keywords = ["bhajan", "mantra", "kirtan", "stotram", "chant", "dharmic", "spiritual", "shiva", "krishna", "devi", "ganesha", "hanuman", "rama", "vedic", "suprabhatam", "chalisa", "jaap"]
        query_lower = query.lower()
        has_spiritual = any(kw in query_lower for kw in spiritual_keywords)
        
        search_query = query
        if not has_spiritual:
            search_query += " bhajan stotram chant"

        spotify_results = []

        # Try Spotify API first if credentials exist
        has_auth = await self._get_access_token()
        if has_auth and self.access_token:
            url = f"https://api.spotify.com/v1/search?q={search_query}&type=track&limit={limit}"
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url, headers=headers)
                    if response.status_code == 200:
                        tracks_data = response.json().get("tracks", {}).get("items", [])
                        for item in tracks_data:
                            track_id = item.get("id")
                            title = item.get("name")
                            artists = ", ".join([a.get("name") for a in item.get("artists", [])])
                            spotify_url = item.get("external_urls", {}).get("spotify", f"https://open.spotify.com/track/{track_id}")
                            duration_ms = item.get("duration_ms", 0)
                            duration_s = int(duration_ms / 1000)
                            
                            # Guess deity/category
                            deity = None
                            for d in ["shiva", "krishna", "devi", "rama", "ganesha", "hanuman"]:
                                if d in title.lower() or d in query_lower:
                                    deity = d.capitalize()
                                    break
                            
                            category = "Bhajan"
                            for c in ["mantra", "chant", "kirtan", "meditation"]:
                                if c in title.lower():
                                    category = c.capitalize()
                                    break
                            
                            spotify_results.append({
                                "title": title,
                                "artist": artists,
                                "url": spotify_url,
                                "category": category,
                                "deity": deity,
                                "duration": duration_s,
                                "lyrics": f"[Spotify Streaming Hymn]\nLyrics study in progress for '{title}'...",
                                "meaning": f"Contemplate this devotional track: {title} by {artists}.",
                                "mood_tags": "calm, bhakti",
                                "spiritual_intensity": 4,
                                "is_mantra_loopable": any(w in title.lower() for w in ["mantra", "loop", "chant", "108"]),
                                "audio_source": "spotify",
                                "authenticity_score": 85
                            })
                    else:
                        logger.error(f"Spotify search request failed: {response.status_code} - {response.text}")
            except Exception as e:
                logger.error(f"Error querying Spotify API: {e}")

        # If Spotify returned ANY results, return them immediately.
        # Do not supplement with YouTube. Only go to YouTube if Spotify returned 0 results.
        if len(spotify_results) > 0:
            return spotify_results

        # Fallback to YouTube as the last option
        youtube_results = []
        try:
            from app.core.youtube_search import search_youtube_spiritual
            yt_results = await search_youtube_spiritual(search_query, max_results=limit)
            for yr in yt_results:
                yt_id = yr["youtube_id"]
                title = yr["title"]
                desc = yr.get("description", "")
                channel = yr.get("channel_name", "YouTube Devotional")
                
                deity = None
                for d in ["shiva", "krishna", "devi", "rama", "ganesha", "hanuman"]:
                    if d in title.lower() or d in query_lower:
                        deity = d.capitalize()
                        break
                        
                category = "Bhajan"
                for c in ["mantra", "chant", "kirtan", "meditation"]:
                    if c in title.lower():
                        category = c.capitalize()
                        break
                        
                youtube_results.append({
                    "title": title,
                    "artist": channel[:45] if channel else "YouTube Devotional",
                    "url": f"https://www.youtube.com/watch?v={yt_id}",
                    "category": category,
                    "deity": deity,
                    "duration": yr.get("duration", 240) or 240,
                    "lyrics": f"[YouTube Devotional Audio]\nListen to: {title}",
                    "meaning": desc[:150] if desc else f"Sattvic recitation of {title}.",
                    "mood_tags": "calm, bhakti",
                    "spiritual_intensity": 4,
                    "is_mantra_loopable": any(w in title.lower() for w in ["mantra", "loop", "chant", "108"]),
                    "audio_source": "youtube",
                    "authenticity_score": 80
                })
        except Exception as e:
            logger.error(f"Spotify search fallback failed: {e}")

        # Combine them: Spotify first, then YouTube
        return spotify_results + youtube_results

spotify_search = SpotifySearchService()
