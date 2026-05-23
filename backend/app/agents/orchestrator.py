import logging
import json
from typing import List, Dict, Any, Optional
from app.agents.base import BaseAgent
from app.agents.dharma_guide import DharmaGuideAgent
from app.agents.scripture_scholar import ScriptureScholarAgent
from app.agents.sadhana_coach import SadhanaCoachAgent
from app.agents.ritual_assistant import RitualAssistantAgent
from app.agents.reflection_journal import ReflectionJournalAgent
from app.core.retrieval import scripture_retrieval_service
from app.core.memory_manager import memory_manager
from app.core.state_engine import state_engine

logger = logging.getLogger("garuda_dharma.orchestrator")

ORCHESTRATOR_PROMPT = """You are the Supreme Orchestrator Agent of Garuda Dharma OS.
Your role is to coordinate the system's subagents, review their answers, and present a coherent, unified response to the user.

Subagents available:
1. Dharma Guide: For emotional, life-ethical advice and applying philosophy to daily struggles.
2. Scripture Scholar: For word-by-word Sanskrit translations, commentary comparisons, and literal text explanations.
3. Sadhana Coach: For designing meditations, breath practices, routine tracks, and habits.
4. Ritual Assistant: For puja setup instructions, fasts (vratas), and traditional festival steps.
5. Reflection Journal: For prompting self-inquiry and analyzing journaling logs.

Safety & Ethics Rules:
- The final response MUST NEVER claim divine authority or claim the AI is enlightened.
- Suggest that the user reflect deeply, discuss with mentors/gurus, and use this system as a reference guide.
- Format the response using clean, Notion-like Markdown formatting, using blockquotes, headers, and code sections where appropriate.
"""

class OrchestratorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Orchestrator",
            system_prompt=ORCHESTRATOR_PROMPT
        )
        # Initialize Subagents
        self.agents = {
            "dharma_guide": DharmaGuideAgent(),
            "scripture_scholar": ScriptureScholarAgent(),
            "sadhana_coach": SadhanaCoachAgent(),
            "ritual_assistant": RitualAssistantAgent(),
            "reflection_journal": ReflectionJournalAgent()
        }

    async def route_and_resolve(
        self, 
        user_id: int,
        query: str, 
        history: Optional[List[Dict[str, str]]] = None,
        db_session = None
    ) -> Dict[str, Any]:
        """
        Coordinates database lookup, memory recall, subagent routing, execution, and synthesis.
        """
        logger.info(f"Orchestrating query: {query}")
        
        # 1. Retrieve User Context (Profile & Spiritual State)
        state_info = "Neutral state"
        deity_pref = "Ganesha"
        philosophy_pref = "Advaita"
        
        if db_session:
            user_profile = state_engine.get_user_profile(user_id, db_session)
            if user_profile:
                deity_pref = user_profile.deity_preference
                philosophy_pref = user_profile.philosophy_preference
            user_state = state_engine.evaluate_spiritual_state(user_id, db_session)
            state_info = user_state.get("state", "calm")

        # 2. Vector DB Retrieval (Scriptures & Saved Memories)
        # We query the retrieval service for matching verses
        retrieved_verses = []
        try:
            retrieved_verses = await scripture_retrieval_service.search_scriptures(query, limit=2)
        except Exception as e:
            logger.error(f"Error during scripture search: {str(e)}")
            
        # Recall memories
        retrieved_memories = []
        if db_session:
            try:
                retrieved_memories = memory_manager.recall_memories(user_id, query, db_session, limit=2)
            except Exception as e:
                logger.error(f"Error recalling memories: {str(e)}")

        # Assemble retrieval context strings
        context_docs = []
        for verse in retrieved_verses:
            context_docs.append(
                f"[Scripture: {verse.get('scripture')}, Ch {verse.get('chapter')}, Vs {verse.get('verse')}]\n"
                f"Sanskrit: {verse.get('sanskrit')}\n"
                f"Translation: {verse.get('translation')}\n"
                f"Commentary summary: {verse.get('commentary', '')}"
            )
            
        for mem in retrieved_memories:
            context_docs.append(f"[Personal Memory ({mem.memory_type})]: {mem.content}")

        # 3. Classify/Route Query
        selected_agent_key = self._classify_intent(query)
        logger.info(f"Routed to subagent: {selected_agent_key}")
        
        agent = self.agents[selected_agent_key]
        
        # Inject state information into prompt context
        state_context = f"\nUser State Info: Current mental state is estimated as '{state_info}'. Deity preference: '{deity_pref}'. Philosophy preference: '{philosophy_pref}'."
        query_with_state = query + state_context

        # 4. Generate Subagent Response
        agent_response = await agent.generate_response(
            user_query=query_with_state, 
            history=history, 
            context_docs=context_docs
        )

        # 5. Review & Format response via Orchestrator Prompt to apply safety constraints
        final_prompt = (
            f"Please format, polish, and safety-filter the following response generated by the "
            f"'{agent.name}' subagent for user query '{query}'. Ensure it adheres to the Guru warning, "
            f"retains all relevant verse references, and presents everything in an elegant, structured format.\n\n"
            f"Subagent Response:\n{agent_response}"
        )
        
        final_response = await self.generate_response(
            user_query=final_prompt,
            history=None,
            context_docs=None
        )

        # Save this interaction as a memory in background if it's significant
        if db_session and len(query) > 10:
            memory_manager.save_memory(
                user_id=user_id,
                memory_type="knowledge",
                content=f"User asked: {query} | Response highlighted: {final_response[:200]}...",
                metadata={"query": query, "agent": agent.name},
                db=db_session
            )

        return {
            "routed_agent": agent.name,
            "response": final_response,
            "detected_state": state_info,
            "verses_cited": [v.get('verse') for v in retrieved_verses if v.get('verse')]
        }

    def _classify_intent(self, query: str) -> str:
        """
        Classifies user query to map to one of our expert subagents.
        Uses robust keyword classification mapping.
        """
        q = query.lower()
        
        # Scripture scholar keywords
        if any(w in q for w in ["verse", "sanskrit", "gita", "upanishad", "translation", "commentary", "shloka", "sloka", "meaning of"]):
            return "scripture_scholar"
            
        # Sadhana Coach keywords
        if any(w in q for w in ["sadhana", "meditate", "meditation", "streak", "japa", "chant", "pranayama", "routine", "habit", "schedule"]):
            return "sadhana_coach"
            
        # Ritual Assistant keywords
        if any(w in q for w in ["puja", "ritual", "vrat", "fasting", "offering", "prasad", "deity", "altar", "festival", "tithi"]):
            return "ritual_assistant"
            
        # Reflection journal keywords
        if any(w in q for w in ["journal", "diary", "reflect", "introspection", "emotion", "feeling", "mood"]):
            return "reflection_journal"
            
        # Default is Dharma Guide for general life / spiritual advice
        return "dharma_guide"
