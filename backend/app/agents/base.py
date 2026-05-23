import httpx
import json
import logging
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger("garuda_dharma.agents")

class BaseAgent:
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL

    async def generate_response(
        self, 
        user_query: str, 
        history: Optional[List[Dict[str, str]]] = None,
        context_docs: Optional[List[str]] = None
    ) -> str:
        """
        Sends the system prompt, chat history, retrieval context, and user query to the local Ollama LLM.
        """
        if history is None:
            history = []
            
        # Build prompt messages
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add retrieval context if present
        if context_docs:
            context_string = "\n---\n".join(context_docs)
            messages.append({
                "role": "system", 
                "content": f"Use the following authentic scriptural and knowledge context to formulate your response. Cite the sources where possible:\n\n{context_string}"
            })
            
        # Append history
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
        # Append user query
        messages.append({"role": "user", "content": user_query})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.3 # Low temperature for accurate scriptural interpretations
            }
        }
        
        url = f"{self.base_url}/api/chat"
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("message", {}).get("content", "").strip()
                else:
                    logger.error(f"Ollama server error: Status {response.status_code}")
                    return self._fallback_response(f"HTTP Error {response.status_code}")
        except httpx.ConnectError:
            logger.warning("Could not connect to Ollama. Make sure Ollama is running.")
            return self._fallback_response("Ollama connection refused. Please start Ollama.")
        except Exception as e:
            logger.error(f"Unexpected error calling Ollama: {str(e)}")
            return self._fallback_response(str(e))

    def _fallback_response(self, error_message: str) -> str:
        """
        Provides a respectful spiritual fallback response when the local LLM is unavailable.
        """
        return (
            f"*[Garuda Dharma OS | Mode: Local Offline]*\n\n"
            f"Hari Om. I am currently unable to query my deep intelligence model ({settings.OLLAMA_MODEL}) "
            f"because: `{error_message}`.\n\n"
            f"Please verify that Ollama is running locally on `{self.base_url}` and has the model pulled "
            f"(`ollama pull {settings.OLLAMA_MODEL}`).\n\n"
            f"In the meantime, seek stability in reflection. Let me know how else I can assist you."
        )

    async def get_embeddings(self, text: str) -> List[float]:
        """
        Generates text embeddings using the configured local embedding model in Ollama.
        """
        url = f"{self.base_url}/api/embeddings"
        payload = {
            "model": settings.OLLAMA_EMBEDDING_MODEL,
            "prompt": text
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    return response.json().get("embedding", [])
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
        
        # Return a zero vector of dimension 768 as fallback
        return [0.0] * 768
