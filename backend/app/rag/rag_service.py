import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings

# Curated, authoritative operational knowledge base for emergency coordination
KNOWLEDGE_BASE_DOCS = [
    {
        "id": "KB-DOC-01",
        "title": "Emergency Department Resource Triage and Queue Disciplines",
        "category": "Operations Research",
        "content": (
            "In emergency healthcare operations, FIFO (First-In, First-Out) queuing can cause fatal "
            "delays for high-acuity resuscitation patients. Priority queuing augmented by starvation "
            "mitigation ensures emergent cases receive immediate resources while capping max wait times."
        )
    },
    {
        "id": "KB-DOC-02",
        "title": "Operational Constraints in Bed Bay Allocation",
        "category": "Facility Logistics",
        "content": (
            "Resuscitation bays are equipped with wall-piped medical gasses, dual-suction, and 360-degree "
            "trauma team clearance. Placing non-urgent patients into resuscitation bays locks out imminent "
            "trauma arrivals, violating the mutual-exclusion and capability-match invariants."
        )
    },
    {
        "id": "KB-DOC-03",
        "title": "Clinical Staffing Ratios & Multi-Skill Constraints",
        "category": "Human Resources",
        "content": (
            "Trauma surgeons and emergency physicians have distinct clinical scopes. FLOWGUARD enforces "
            "deterministic matching so that critical resuscitation cases require credentialed trauma surgeons, "
            "while acute monitored patients are attended by emergency physicians or ICU-certified nurses."
        )
    },
    {
        "id": "KB-DOC-04",
        "title": "Dynamic Replanning Following Resource Disruption",
        "category": "System Architecture",
        "content": (
            "When beds or equipment go offline (due to sanitation, mechanical failure, or diversion), the agent "
            "must immediately recalculate feasible allocations across the remaining queue. Cases blocked by missing "
            "equipment must be explicitly flagged with actionable rejection rationale."
        )
    },
    {
        "id": "KB-DOC-05",
        "title": "Non-Clinical Scope & Safety Boundary Disclaimer",
        "category": "Governance",
        "content": (
            "FLOWGUARD is strictly an operational logistics coordination prototype for simulated emergency "
            "departments. It never provides medical diagnoses, pharmacological advice, or patient discharge instructions. "
            "All final clinical decisions remain the responsibility of licensed healthcare personnel."
        )
    }
]

class LocalRAGService:
    """
    Lightweight, dependable local retrieval engine with optional Ollama LLM integration.
    Gracefully degrades to deterministic explanation when Ollama is offline or unconfigured.
    """

    @classmethod
    def retrieve_relevant_passages(cls, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        query_terms = set(query.lower().split())
        scored = []
        for doc in KNOWLEDGE_BASE_DOCS:
            text = (doc["title"] + " " + doc["content"]).lower()
            score = sum(1 for term in query_terms if term in text)
            if score > 0:
                scored.append((score, doc))
        
        scored.sort(key=lambda x: -x[0])
        results = [doc for _, doc in scored[:top_k]]
        if not results:
            results = KNOWLEDGE_BASE_DOCS[:top_k]
        return results

    @classmethod
    async def check_ollama_health(cls) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                if res.status_code == 200:
                    models_info = res.json()
                    models = [m.get("name") for m in models_info.get("models", [])]
                    model_available = any(settings.OLLAMA_MODEL in m for m in models)
                    return {
                        "available": True,
                        "model_configured": settings.OLLAMA_MODEL,
                        "model_present": model_available,
                        "available_models": models
                    }
        except Exception:
            pass
        return {
            "available": False,
            "model_configured": settings.OLLAMA_MODEL,
            "model_present": False,
            "available_models": []
        }

    @classmethod
    async def generate_explanation(
        cls, 
        query: str, 
        decision_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        passages = cls.retrieve_relevant_passages(query)
        sources = [{"id": p["id"], "title": p["title"], "category": p["category"]} for p in passages]

        health = await cls.check_ollama_health()
        
        # Build prompt context
        context_str = "\n".join([f"[{p['title']}]: {p['content']}" for p in passages])
        deterministic_fallback = (
            f"Deterministic Operational Explanation:\n"
            f"Based on emergency queue policies and operational constraint evaluation, "
            f"resources are prioritized strictly by clinical urgency score followed by queued wait-time. "
            f"Referenced Guidelines:\n- " + "\n- ".join([f"{p['title']}: {p['content']}" for p in passages])
        )

        if not health["available"] or not health["model_present"]:
            return {
                "explanation": deterministic_fallback,
                "is_llm_generated": False,
                "model_used": "Deterministic Rule-Engine Fallback",
                "sources": sources,
                "ollama_status": "Ollama service unavailable or model not loaded. Deterministic reasoning active."
            }

        # Attempt Ollama local generation with generous timeout for initial model warm-up
        prompt = (
            f"You are FLOWGUARD's operational explainability assistant. Explain the following emergency department "
            f"allocation decision clearly, factually, and grounded ONLY in the retrieved operational documentation.\n\n"
            f"Documentation:\n{context_str}\n\n"
            f"Query / Decision: {query}\n"
            f"Decision Context: {decision_context or 'Standard queue allocation'}\n\n"
            f"Provide a concise, 2-paragraph professional operational summary. Do NOT make clinical or medical recommendations."
        )

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                if resp.status_code == 200:
                    text = resp.json().get("response", "").strip()
                    return {
                        "explanation": text,
                        "is_llm_generated": True,
                        "model_used": settings.OLLAMA_MODEL,
                        "sources": sources,
                        "ollama_status": "Connected to local Ollama inference server."
                    }
        except Exception as e:
            pass

        return {
            "explanation": deterministic_fallback,
            "is_llm_generated": False,
            "model_used": "Deterministic Rule-Engine Fallback",
            "sources": sources,
            "ollama_status": "Ollama warm-up/timeout. Deterministic fallback engaged."
        }
