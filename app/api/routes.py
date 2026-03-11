from fastapi import APIRouter, Depends, BackgroundTasks, Request, Header, HTTPException
from fastapi.responses import FileResponse
from loguru import logger
from typing import Optional, Dict, Any
import os, asyncio, threading, mimetypes
from cachetools import TTLCache
from app.agents.orchestrator import TravelAgent
from app.services.user_service import UserService
from app.config import settings

router = APIRouter()
_agent = None
_agent_lock = threading.Lock()
_locks_cache = TTLCache(maxsize=5000, ttl=300)
_locks_cache_lock = threading.Lock()

def get_agent() -> TravelAgent:
    global _agent
    if _agent is None:
        with _agent_lock:
            if _agent is None: _agent = TravelAgent()
    return _agent

def get_lock(key: str) -> asyncio.Lock:
    with _locks_cache_lock:
        if key not in _locks_cache: _locks_cache[key] = asyncio.Lock()
        return _locks_cache[key]

@router.post("/webhook/whatsapp")
async def unified_whatsapp_webhook(request: Request, background_tasks: BackgroundTasks, agent: TravelAgent = Depends(get_agent)):
    try:
        payload = await request.json()
        data = payload.get("data", payload)
        key = data.get("key", {})
        if key.get("fromMe"): return {"status": "ignored"}
        user_id = key.get("remoteJid", "").split("@")[0]
        user_service = UserService()
        normalized_id = user_service.normalize_phone(user_id)
        active_trip_id = user_service.get_active_trip(normalized_id)
        
        event = {"user_id": normalized_id, "trip_id": active_trip_id, "payload": data}
        background_tasks.add_task(run_agent_event, normalized_id, event, agent)
        return {"status": "queued", "trip": active_trip_id}
    except Exception as e:
        logger.error(f"Erro Gateway: {e}")
        return {"status": "error"}

async def run_agent_event(user_id: str, event: Dict[str, Any], agent: TravelAgent):
    async with get_lock(user_id):
        try:
            await agent.run_event(event)
        except Exception as e:
            logger.error(f"Erro Evento {user_id}: {e}")

@router.get("/health")
async def health(): return {"status": "online", "engine": "Antigravity 8.0"}
