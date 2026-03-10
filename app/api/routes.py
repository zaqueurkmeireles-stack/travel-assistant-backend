"""
API Routes - TravelCompanion AI
Versão: Antigravity 7.0 (Enterprise Fortress)
Data: 2026-03-10
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
from loguru import logger
from typing import Optional, Tuple, Dict, Any
from cachetools import TTLCache
import os
import asyncio
import threading
import mimetypes

# Imports de Serviços
from app.agents.orchestrator import TravelAgent
from app.services.document_ingestor import DocumentIngestor
from app.services.n8n_service import N8nService
from app.config import settings
from app.services.idempotency_service import IdempotencyService
from app.services.user_service import UserService

router = APIRouter()

# --- VALIDADOES REUTILIZÁVEIS ---

def validate_phone_id(v: str) -> str:
    if not v or not v.strip():
        raise ValueError("user_id é obrigatório e não pode ser vazio")
    return v.strip()

# --- MODELOS DE DADOS ---

class ChatRequest(BaseModel):
    user_id: str
    message: str
    message_id: Optional[str] = None 
    push_name: Optional[str] = "Desconhecido"
    
    _val_user = field_validator('user_id')(validate_phone_id)

    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str):
        if len(v) > 4096:
            raise ValueError("Mensagem excede o limite de 4096 caracteres")
        return v.strip()

class ChatResponse(BaseModel):
    success: bool
    response: str
    user_id: str

class LocationRequest(BaseModel):
    user_id: str
    latitude: float
    longitude: float
    
    _val_user = field_validator('user_id')(validate_phone_id)

    @field_validator('latitude')
    @classmethod
    def validate_lat(cls, v: float):
        if not -90 <= v <= 90:
            raise ValueError("Latitude deve estar entre -90 e 90")
        return v

    @field_validator('longitude')
    @classmethod
    def validate_long(cls, v: float):
        if not -180 <= v <= 180:
            raise ValueError("Longitude deve estar entre -180 e 180")
        return v

class MediaRequest(BaseModel):
    user_id: str
    message_id: Optional[str] = None 
    base64: str = ""
    filename: str = "arquivo"
    mimetype: str = "application/octet-stream"
    
    _val_user = field_validator('user_id')(validate_phone_id)

    @field_validator('base64')
    @classmethod
    def validate_base64_size(cls, v: str):
        # Cálculo dinâmico: 50MB + overhead Base64
        limit_mb = 50
        max_chars = int(limit_mb * 1024 * 1024 * 1.34)
        if len(v) > max_chars:
            raise ValueError(f"Arquivo excede o limite de {limit_mb}MB")
        return v

# --- GESTÃO DE ESTADO (Thread-Safe) ---

_agent = None
_idempotency = None
_agent_lock = threading.Lock()
_idempotency_lock = threading.Lock()
_locks_cache = TTLCache(maxsize=5000, ttl=300)
_locks_cache_lock = threading.Lock()

def get_idempotency_service() -> IdempotencyService:
    global _idempotency
    if _idempotency is None:
        with _idempotency_lock:
            if _idempotency is None:
                _idempotency = IdempotencyService()
    return _idempotency

def get_lock(key: str) -> asyncio.Lock:
    with _locks_cache_lock:
        if key not in _locks_cache:
            _locks_cache[key] = asyncio.Lock()
        return _locks_cache[key]

def get_agent() -> TravelAgent:
    global _agent
    if _agent is None:
        with _agent_lock:
            if _agent is None:
                _agent = TravelAgent()
    return _agent

# --- ENDPOINTS ---

@router.get("/health")
async def health_check():
    return {"status": "ok", "version": "7.0", "engine": "Antigravity"}

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    agent: TravelAgent = Depends(get_agent),
    idempotency: IdempotencyService = Depends(get_idempotency_service)
):
    user_service = UserService()
    try:
        request.user_id = user_service.normalize_phone(request.user_id)
    except ValueError:
        return ChatResponse(success=True, response="Formato inválido", user_id="error")

    id_key = idempotency.generate_key(request.user_id, request.message_id, request.message)
    if idempotency.check_and_register(id_key, request.user_id, request.message_id, request.dict()):
        return ChatResponse(success=True, response="Processando...", user_id=request.user_id)

    background_tasks.add_task(process_chat_message, request, agent, id_key, idempotency)
    return ChatResponse(success=True, response="Processando...", user_id=request.user_id)

async def process_chat_message(request: ChatRequest, agent: TravelAgent, id_key: str, idempotency: IdempotencyService):
    async with get_lock(request.user_id):
        idempotency.update_status(id_key, "PROCESSING")
        try:
            user_service = UserService()
            active_trip = user_service.get_active_trip(request.user_id)
            auth = user_service.authorize(request.user_id, active_trip, scope="ask")
            
            if not auth[0]:
                idempotency.update_status(id_key, "RESPONDED", response="Acesso negado")
                return

            resposta = await asyncio.wait_for(
                asyncio.to_thread(agent.chat, user_input=request.message, thread_id=request.user_id),
                timeout=45.0
            )
            
            if resposta:
                await asyncio.to_thread(N8nService().enviar_resposta_usuario, request.user_id, resposta, True)
            idempotency.update_status(id_key, "RESPONDED", response=resposta)
        except Exception as e:
            logger.error(f"❌ Erro Chat: {e}")
            idempotency.update_status(id_key, "FAILED", error_msg=str(e))

@router.post("/webhook/media")
async def media_webhook(
    request: MediaRequest, 
    background_tasks: BackgroundTasks,
    idempotency: IdempotencyService = Depends(get_idempotency_service)
):
    user_service = UserService()
    try:
        request.user_id = user_service.normalize_phone(request.user_id)
    except ValueError:
        return {"success": True}

    id_key = idempotency.generate_key(request.user_id, request.message_id, media_hash=request.filename)
    if idempotency.check_and_register(id_key, request.user_id, request.message_id, request.dict()):
        return {"success": True}

    background_tasks.add_task(process_media_webhook, request, id_key, idempotency)
    return {"success": True}

async def process_media_webhook(request: MediaRequest, id_key: str, idempotency: IdempotencyService):
    async with get_lock(request.user_id):
        idempotency.update_status(id_key, "PROCESSING")
        try:
            user_service = UserService()
            active_trip = user_service.get_active_trip(request.user_id)
            if not user_service.authorize(request.user_id, active_trip, scope="upload")[0]:
                idempotency.update_status(id_key, "RESPONDED", response="Negado")
                return

            payload = {
                "key": {"remoteJid": f"{request.user_id}@s.whatsapp.net", "id": request.message_id},
                "message": {"documentMessage": {"fileName": request.filename, "mimetype": request.mimetype}},
                "base64": request.base64, "message_id": request.message_id
            }
            
            result = await asyncio.wait_for(
                asyncio.to_thread(DocumentIngestor().ingest_from_webhook, payload),
                timeout=60.0
            )
            
            if result.get("success"):
                msg = f"✅ Arquivo {request.filename} salvo!"
                await asyncio.to_thread(N8nService().enviar_resposta_usuario, request.user_id, msg, True)
                idempotency.update_status(id_key, "RESPONDED")
        except Exception as e:
            logger.error(f"❌ Erro Media: {e}")
            idempotency.update_status(id_key, "FAILED", error_msg=str(e))

@router.post("/webhook/location")
async def location_webhook(
    request: LocationRequest, 
    background_tasks: BackgroundTasks, 
    agent: TravelAgent = Depends(get_agent),
    idempotency: IdempotencyService = Depends(get_idempotency_service)
):
    user_service = UserService()
    try:
        request.user_id = user_service.normalize_phone(request.user_id)
    except ValueError:
        return {"success": True}
    
    # [CORREÇÃO] Idempotência de Localização (Arredondamento de 4 casas = ~11 metros)
    geo_hash = f"{round(request.latitude, 4)}_{round(request.longitude, 4)}"
    id_key = idempotency.generate_key(request.user_id, "location_update", geo_hash)
    
    if idempotency.check_and_register(id_key, request.user_id, "location", request.dict()):
        return {"success": True}
        
    background_tasks.add_task(process_location_webhook, request, agent)
    return {"success": True}

async def process_location_webhook(request: LocationRequest, agent: TravelAgent):
    try:
        user_service = UserService()
        active_trip = user_service.get_active_trip(request.user_id)
        if not user_service.authorize(request.user_id, active_trip, scope="location")[0]:
            return
        
        from app.services.maps_service import GoogleMapsService
        geo = await asyncio.wait_for(
            asyncio.to_thread(GoogleMapsService().reverse_geocode, request.latitude, request.longitude),
            timeout=10.0
        )
        
        res = await asyncio.to_thread(agent.chat, user_input=f"SISTEMA: Usuário em {geo}", thread_id=request.user_id)
        if res and "IGNORE" not in res:
            await asyncio.to_thread(N8nService().enviar_resposta_usuario, request.user_id, res, True)
            
    except Exception as e:
        logger.error(f"❌ Erro Localização: {e}")

@router.get("/documents/{filename}")
async def get_document_file(filename: str, user_id: str, x_api_token: Optional[str] = Header(None)):
    token = os.getenv("INTERNAL_API_TOKEN")
    if not token or x_api_token != token:
        raise HTTPException(status_code=403, detail="Acesso Proibido")

    user_service = UserService()
    safe_name = os.path.basename(filename)
    if not user_service.owns_document(user_id, safe_name):
        raise HTTPException(status_code=403)

    path = os.path.join(settings.DOCUMENTS_PATH, safe_name)
    if not os.path.exists(path): raise HTTPException(status_code=404)

    ctype, _ = mimetypes.guess_type(path)
    return FileResponse(path, media_type=ctype or "application/octet-stream", filename=safe_name)
