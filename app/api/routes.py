"""
API Routes - Endpoints REST para o TravelCompanion AI
Versão: Antigravity 2.0 (Stable & Clean)
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from loguru import logger
from typing import Optional, Dict, Any, List
import os
import httpx
import asyncio

# Imports de Serviços
from app.parsers.parser_factory import ParserFactory
from app.agents.orchestrator import TravelAgent
from app.services.document_ingestor import DocumentIngestor
from app.services.n8n_service import N8nService
from app.config import settings
from app.services.idempotency_service import IdempotencyService
from app.services.user_service import UserService

router = APIRouter()

# --- MODELOS ---
class ChatRequest(BaseModel):
    user_id: str
    message: str
    message_id: Optional[str] = None 
    push_name: Optional[str] = "Desconhecido"

class ChatResponse(BaseModel):
    success: bool
    response: str
    user_id: str

class LocationRequest(BaseModel):
    user_id: str
    latitude: float
    longitude: float
    address: Optional[str] = None

class MediaRequest(BaseModel):
    user_id: str
    message_id: Optional[str] = None 
    base64: Optional[str] = ""
    filename: Optional[str] = "arquivo"
    mimetype: Optional[str] = "application/octet-stream"
    push_name: Optional[str] = "Desconhecido"

# --- DEPENDÊNCIAS ---
_agent = None
_idempotency = None
_locks: Dict[str, asyncio.Lock] = {}

def get_idempotency() -> IdempotencyService:
    global _idempotency
    if _idempotency is None: _idempotency = IdempotencyService()
    return _idempotency

def get_lock(key: str) -> asyncio.Lock:
    if key not in _locks: _locks[key] = asyncio.Lock()
    return _locks[key]

def get_agent() -> TravelAgent:
    global _agent
    if _agent is None: _agent = TravelAgent()
    return _agent

# --- ENDPOINTS ---

@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "Antigravity is Online"}

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    agent: TravelAgent = Depends(get_agent)
):
    user_service = UserService()
    user_id_raw = request.user_id 
    
    if not request.user_id:
        return ChatResponse(success=True, response="", user_id="error")

    idempotency = get_idempotency()
    request.user_id = user_service.normalize_phone(request.user_id)
    idempotency_key = idempotency.generate_key(request.user_id, request.message_id, request.message)
    
    status = idempotency.check_and_register(idempotency_key, request.user_id, request.message_id, request.dict())
    if status: return ChatResponse(success=True, response="Processando...", user_id=request.user_id)

    try:
        logger.info(f"📡 [INCOMING] {user_id_raw} -> {request.user_id}")
        if "@g.us" in user_id_raw:
            idempotency.update_status(idempotency_key, "RESPONDED", response="Grupo ignorado")
            return ChatResponse(success=True, response="", user_id=request.user_id)

        background_tasks.add_task(process_chat_message, request, agent, idempotency_key)
        return ChatResponse(success=True, response="Processando...", user_id=request.user_id)
    except Exception as e:
        logger.error(f"❌ Erro chat: {e}")
        return ChatResponse(success=False, response=str(e), user_id=request.user_id)

async def process_chat_message(request: ChatRequest, agent: TravelAgent, idempotency_key: str):
    idempotency = get_idempotency()
    async with get_lock(request.user_id):
        idempotency.update_status(idempotency_key, "PROCESSING")
        try:
            user_service = UserService()
            active_trip = user_service.get_active_trip(request.user_id)
            auth = user_service.authorize(request.user_id, active_trip, scope="ask")
            
            if not auth.get("allowed", False):
                if auth.get("reason") == "Usuário não cadastrado ou não autorizado.":
                    user_service.register_access_request(request.user_id, request.push_name)
                return

            resposta_ia = agent.chat(user_input=request.message, thread_id=request.user_id)
            if resposta_ia:
                N8nService().enviar_resposta_usuario(request.user_id, resposta_ia, bypass_firewall=True)
            idempotency.update_status(idempotency_key, "RESPONDED", response=resposta_ia)
        except Exception as e:
            idempotency.update_status(idempotency_key, "FAILED", error_msg=str(e))

@router.post("/webhook/media")
async def media_webhook(request: MediaRequest, background_tasks: BackgroundTasks):
    user_service = UserService()
    idempotency = get_idempotency()
    request.user_id = user_service.normalize_phone(request.user_id)
    idempotency_key = idempotency.generate_key(request.user_id, request.message_id, media_hash=request.filename)
    
    if idempotency.check_and_register(idempotency_key, request.user_id, request.message_id, request.dict()):
        return {"success": True}

    background_tasks.add_task(process_media_webhook, request, idempotency_key)
    return {"success": True}

async def process_media_webhook(request: MediaRequest, idempotency_key: str):
    idempotency = get_idempotency()
    async with get_lock(request.user_id):
        idempotency.update_status(idempotency_key, "PROCESSING")
        try:
            user_service = UserService()
            ingestor = DocumentIngestor()
            data_payload = {
                "key": {"remoteJid": f"{request.user_id}@s.whatsapp.net", "id": request.message_id},
                "message": {"documentMessage": {"fileName": request.filename, "mimetype": request.mimetype}},
                "base64": request.base64, "message_id": request.message_id
            }
            result = ingestor.ingest_from_webhook(data_payload)
            
            is_travel = result.get("is_travel_content", True)
            if not is_travel or result.get("status") == "irrelevant":
                msg = f"🤖 O arquivo *{request.filename}* não parece ser de viagem. Salvar mesmo assim? (sim/não)"
                user_service.set_pending_irrelevancy(request.user_id, result)
                N8nService().enviar_resposta_usuario(request.user_id, msg, bypass_firewall=True)
                return 

            if result.get("success"):
                N8nService().enviar_resposta_usuario(request.user_id, f"✅ Documento *{request.filename}* salvo!", bypass_firewall=True)
                idempotency.update_status(idempotency_key, "RESPONDED")
        except Exception as e:
            idempotency.update_status(idempotency_key, "FAILED", error_msg=str(e))

@router.post("/webhook/location")
async def location_webhook(request: LocationRequest, background_tasks: BackgroundTasks, agent: TravelAgent = Depends(get_agent)):
    background_tasks.add_task(process_location_webhook, request, agent)
    return {"success": True}

async def process_location_webhook(request: LocationRequest, agent: TravelAgent):
    try:
        user_service = UserService()
        if user_service.get_user_role(request.user_id) == "unauthorized": return
        from app.services.maps_service import GoogleMapsService
        geo_info = GoogleMapsService().reverse_geocode(request.latitude, request.longitude)
        response = agent.chat(user_input=f"SISTEMA: Usuário em {geo_info}", thread_id=request.user_id)
        if response and "IGNORE" not in response:
            N8nService().enviar_resposta_usuario(request.user_id, response)
    except Exception as e:
        logger.error(f"❌ Erro Geoguia: {e}")

@router.get("/map/data")
async def get_map_data(user_id: str):
    return {"success": True, "data": []}

@router.get("/documents/{filename}")
async def get_document_file(filename: str):
    from fastapi.responses import FileResponse
    file_path = os.path.join(settings.DOCUMENTS_PATH, filename)
    if os.path.exists(file_path): return FileResponse(file_path)
    raise HTTPException(status_code=404)
