"""
akira_api.py  —  Production FastAPI for Akira Real Estate Intelligence
=====================================================================
Exposes Akira's Hybrid RAG as a REST API for Web & Mobile integration.
"""

import os
import uuid
import logging
from typing import List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware

# Import core Akira logic from existing pipeline
from rag_pipeline import (
    RAGConfig, _hf_login, auto_ingest_data, load_data, 
    check_system_memory, load_llm, load_embedding_model,
    process_query, QueryCache
)

# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("akira.api")

# ─────────────────────────────────────────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str = Field(..., example="What are the current land prices in Dubai Marina?")
    session_id: Optional[str] = Field(None, description="Unique ID for conversation history tracking")

class DataPoint(BaseModel):
    point: str

class AkiraResponse(BaseModel):
    session_id: str
    conversational_response: str
    verdict: str
    confidence: int
    key_finding: str
    data_points: List[str]
    evidence_quote: str
    overall_explanation: str

# ─────────────────────────────────────────────────────────────────────────────
# APP STATE
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(title="Akira Real Estate API", version="1.1")

# Enable CORS for Web Integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your website domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables to hold models and indices
state = {
    "cfg": None,
    "index": None,
    "bm25": None,
    "chunks": None,
    "tokenizer": None,
    "llm": None,
    "emb_model": None,
    "cache": None,
    "histories": {} # session_id -> list of history turns
}

@app.on_event("startup")
async def startup_event():
    log.info("Initializing Akira Intelligence Engine...")
    
    cfg = RAGConfig()
    cfg.validate()
    state["cfg"] = cfg
    
    _hf_login()
    
    # Auto-ingest any local data files
    auto_ingest_data(cfg)
    
    # Load Retrieval Engines
    index, bm25, chunks = load_data(cfg.index_dir)
    state["index"] = index
    state["bm25"] = bm25
    state["chunks"] = chunks
    
    # Load Models
    model_id, torch_dtype = check_system_memory()
    tokenizer, llm = load_llm(model_id, torch_dtype, cfg)
    state["tokenizer"] = tokenizer
    state["llm"] = llm
    state["emb_model"] = load_embedding_model()
    
    # Load Cache
    state["cache"] = QueryCache(cfg.cache_path)
    
    log.info("Akira is online and ready for web requests.")

# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
async def health_check():
    return {"status": "online", "model": "Gemma-3", "agent": "Akira"}

@app.post("/ask", response_model=AkiraResponse)
async def ask_akira(request: QueryRequest):
    if not state["llm"]:
        raise HTTPException(status_code=503, detail="Akira engine is still starting up.")
    
    # Handle Session ID for Conversation History
    session_id = request.session_id or str(uuid.uuid4())
    if session_id not in state["histories"]:
        state["histories"][session_id] = []
    
    history = state["histories"][session_id]
    
    try:
        # We need the structured JSON back for the API, but process_query displays it.
        # Let's import the specific pieces needed to run the logic without CLI prints.
        from rag_pipeline import (
            retrieve, format_prompt, 
            generate_answer, clean_and_parse,
            ScraperBridge
        )
        
        # 1. Check Cache
        cached = state["cache"].get(request.query)
        if cached:
            log.info(f"Cache hit for session {session_id}")
            return {**cached, "session_id": session_id}

        # 2. Hybrid Retrieval
        context_items = retrieve(
            request.query, state["emb_model"], state["index"], 
            state["bm25"], state["chunks"], state["cfg"]
        )
        
        # Proper call to bridge for context
        hybrid_context = ScraperBridge(state["cfg"]).get_hybrid_context(request.query)

        # 3. Build Prompt with History
        prompt = format_prompt(request.query, context_items, hybrid_context, history=history)

        # 4. Generate
        raw_answer = generate_answer(prompt, state["tokenizer"], state["llm"], state["cfg"])
        
        # 5. Parse
        parsed = clean_and_parse(raw_answer)
        
        # 6. Update Cache and History
        state["cache"].set(request.query, parsed)
        
        # Store a string version for history
        history_entry = f"{parsed.get('conversational_response', '')} {parsed.get('overall_explanation', '')}"
        state["histories"][session_id].append({"user": request.query, "assistant": history_entry})
        if len(state["histories"][session_id]) > 5:
            state["histories"][session_id].pop(0)
            
        return {**parsed, "session_id": session_id}

    except Exception as e:
        log.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest")
async def trigger_ingestion(background_tasks: BackgroundTasks):
    """Manually trigger a re-scan of the directory for new PDF/CSV files."""
    background_tasks.add_task(auto_ingest_data, state["cfg"])
    return {"message": "Data ingestion started in the background."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
