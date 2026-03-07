"""
API Routes - Endpoints REST para o TravelCompanion AI
Conecta o agente LangGraph e os Parsers ao mundo externo (n8n/WhatsApp)
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from loguru import logger
from typing import Optional

# Imports dos nossos motores
from app.parsers.parser_factory import ParserFactory
from app.agents.orchestrator import TravelAgent
from app.services.document_ingestor import DocumentIngestor
from app.services.n8n_service import N8nService
from app.config import settings
from app.services.idempotency_service import IdempotencyService
import httpx
import asyncio

router = APIRouter()

# ============================================================
# MODELOS DE DADOS (Pydantic)
# ============================================================
class ChatRequest(BaseModel):
    user_id: str  # Número do WhatsApp (usado como thread_id na memória)
    message: str  # Mensagem do usuário
    message_id: Optional[str] = None # ID único da mensagem para evitar duplicatas
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
    message_id: Optional[str] = None # ID único da mensagem para evitar duplicatas
    base64: Optional[str] = ""
    filename: Optional[str] = "arquivo"
    mimetype: Optional[str] = "application/octet-stream"
    push_name: Optional[str] = "Desconhecido"

# ============================================================
# CACHE DE DEDUPLICAÇÃO (Evita processar a mesma mensagem 2x)
# ============================================================
from cachetools import TTLCache
# Mantém 1000 IDs de mensagens por 60 segundos
_dedup_cache = TTLCache(maxsize=1000, ttl=60)

# ============================================================
# GERENCIAMENTO DE DEPENDÊNCIAS (Singletons para Performance)
# ============================================================
_agent = None
_parser_factory = None
_idempotency = None
_locks: Dict[str, asyncio.Lock] = {}

def get_idempotency() -> IdempotencyService:
    global _idempotency
    if _idempotency is None:
        _idempotency = IdempotencyService()
    return _idempotency

def get_lock(key: str) -> asyncio.Lock:
    if key not in _locks:
        _locks[key] = asyncio.Lock()
    return _locks[key]

def get_agent() -> TravelAgent:
    """Retorna a instância global do TravelAgent (evita recompilar o grafo a cada request)"""
    global _agent
    if _agent is None:
        logger.info("⚙️ Inicializando TravelAgent para a API...")
        _agent = TravelAgent()
    return _agent

def get_parser_factory() -> ParserFactory:
    """Retorna a instância global da ParserFactory"""
    global _parser_factory
    if _parser_factory is None:
        logger.info("⚙️ Inicializando ParserFactory para a API...")
        _parser_factory = ParserFactory()
    return _parser_factory


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/")
@router.get("/health")
async def health_check():
    """Endpoint for platforms like Easypanel to verify the app is alive."""
    return JSONResponse(content={"status": "ok", "message": "TravelCompanion AI is running"})

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    agent: TravelAgent = Depends(get_agent)
):
    """
    Endpoint principal de Chat (Webhook para n8n/WhatsApp)
    Recebe a mensagem, valida e responde imediatamente com sucesso.
    O processamento real acontece em background para evitar timeouts no n8n.
    """
    if not request.user_id or request.user_id.strip() == "":
        logger.error("❌ Erro: Request recebido com user_id vazio. Verifique o mapeamento no n8n.")
        return ChatResponse(success=True, response="", user_id="desconhecido")
    
    # --- [IDEMPOTÊNCIA] ---
    idempotency = get_idempotency()
    # Gera chave determinística baseada na mensagem se o ID não existir
    # Mas a Evolution sempre deve mandar message_id
    idempotency_key = idempotency.generate_key(request.user_id, request.message_id, request.message)
    
    existing_status = idempotency.check_and_register(
        idempotency_key=idempotency_key, 
        chat_id=request.user_id, 
        message_id=request.message_id,
        payload=request.dict()
    )

    if existing_status:
        if existing_status == "PROCESSING":
            logger.warning(f"⏳ Mensagem em processamento: {idempotency_key}")
            return ChatResponse(success=True, response="Aguarde, processando...", user_id=request.user_id)
        elif existing_status in ["SUCCEEDED", "RESPONDED"]:
            logger.info(f"♻️ Idempotência: Mensagem já processada: {idempotency_key}")
            return ChatResponse(success=True, response="Já processado", user_id=request.user_id)
    
    # Se chegamos aqui, o status é RECEIVED e fomos registrados agora.
    
    try:
        from app.services.user_service import UserService
        user_service = UserService()
        
        # 🛡️ NORMALIZAÇÃO IMEDIATA
        user_id_raw = request.user_id
        request.user_id = user_service.normalize_phone(request.user_id)
        
        logger.info(f"📡 [INCOMING] Recebido: {request.user_id} (Original: {user_id_raw})")
        
        # --- FILTRO DE GRUPOS (SEGURANÇA EXTRA) ---
        if "@g.us" in user_id_raw:
            logger.info(f"👥 Grupo detectado e ignorado: {user_id_raw}")
            idempotency.update_status(idempotency_key, "RESPONDED", response="Grupo ignorado")
            return ChatResponse(success=True, response="", user_id=request.user_id)
        
        if not request.user_id:
            idempotency.update_status(idempotency_key, "FAILED", error_msg="ID inválido")
            return ChatResponse(success=True, response="", user_id="invalid")

        # 🛑 PREVENÇÃO EVOLUTION API: Ignorar mensagens vazias
        if not request.message or not request.message.strip():
            logger.info(f"🛑 [FILTRO] Mensagem vazia de {request.user_id}")
            idempotency.update_status(idempotency_key, "RESPONDED", response="Vazio ignorado")
            return ChatResponse(success=True, response="", user_id=request.user_id)

        # 🛑 PREVENÇÃO DE LOOP INFINITO: Ignorar mensagens enviadas pelo próprio bot
        bot_number = user_service.normalize_phone(getattr(settings, "BOT_WHATSAPP_NUMBER", ""))
        if bot_number and (request.user_id == bot_number or (len(bot_number) >= 8 and request.user_id.endswith(bot_number[-8:]))):
            logger.info("🛑 Mensagem ignorada: Remetente é o próprio bot.")
            idempotency.update_status(idempotency_key, "RESPONDED", response="Bot eco ignorado")
            return ChatResponse(success=True, response="", user_id=request.user_id)

        # Agenda o processamento pesado
        background_tasks.add_task(process_chat_message, request, agent, idempotency_key)
        
        return ChatResponse(
            success=True,
            response="Processando...",
            user_id=request.user_id
        )
    except Exception as e:
        logger.error(f"❌ Erro ao receber chat: {e}")
        idempotency.update_status(idempotency_key, "FAILED", error_msg=str(e))
        return ChatResponse(success=False, response=str(e), user_id=request.user_id)

async def process_chat_message(request: ChatRequest, agent: TravelAgent, idempotency_key: str):
    """Lógica de processamento de chat executada em background"""
    from datetime import datetime
    idempotency = get_idempotency()
    correlation_id = idempotency.get_correlation_id(idempotency_key)
    
    # --- [LOCK POR USUÁRIO] ---
    lock = get_lock(request.user_id)
    async with lock:
        idempotency.update_status(idempotency_key, "PROCESSING")
        try:
            from app.services.user_service import UserService
            user_service = UserService()
            
            message_str = request.message.strip()
            
            # [DIAGNOSTICO] Logar todos os contatos
            try:
                with open("data/contact_history.txt", "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().isoformat()} | ID: {request.user_id} | MSG: {message_str[:50]}...\n")
            except: pass
            
            # --- NOVO: FILTRO DE GRUPOS ---
            if "@g.us" in request.user_id:
                logger.info(f"👥 Grupo detectado e ignorado: {request.user_id}")
                idempotency.update_status(idempotency_key, "RESPONDED", response="Grupo ignorado")
                return

            # 🛑 PREVENÇÃO DE ECO (FORK BOMB)
            bot_signatures = [
                "BEM-VINDO AO SEVEN ASSISTANT TRAVEL", "Pedido de Acesso!", "seven assistant",
                "Aqui estão os detalhes da sua viagem", "Aqui estão os documentos de viagem",
                "Aqui estão os documentos salvos", "Não vejo novos bilhetes de passagem",
                "✅ Documento recebido e salvo!", "📋 Checklist de documentos:",
                "🎉 Todos os documentos essenciais já estão salvos", "🔗 Viagem em Grupo Detectada!",
                "📋 *Checklist de documentos:*", "Sucesso no n8n para", "Resumo da Comunidade:",
                "Como posso ajudar com a viagem hoje?"
            ]
            if any(sig.lower() in message_str.lower() for sig in bot_signatures) and len(message_str) > 20:
                logger.info(f"🛑 Mensagem ignorada: Detectado ECHO ({message_str[:30]}...)")
                return

            role = user_service.get_user_role(request.user_id)
            
            # --- Lógica de Confirmação de Vinculação Automática (SIM/NÃO) ---
            pending_link = user_service.get_pending_trip_link(request.user_id)
            
            # --- Lógica de INCLUSÃO FORÇADA DE ARQUIVO IRRELEVANTE ---
            pending_irr = user_service.get_pending_irrelevancy(request.user_id)
            if pending_irr and message_str.lower() in ["sim", "s", "yes", "sim incluir", "incluir"]:
                logger.info(f"✅ Usuário forçou a inclusão do documento irrelevante: {pending_irr.get('filename')}")
                user_service.clear_pending_irrelevancy(request.user_id)
                
                from app.services.rag_service import RAGService
                rag_svc = RAGService()
                
                extracted_text = pending_irr.get("text", "")
                metadata = pending_irr.get("metadata", {})
                
                # Chunking manual e indexação
                chunk_size = 4000
                overlap = 200
                chunks = [extracted_text[i:i + chunk_size] for i in range(0, max(1, len(extracted_text)), chunk_size - overlap)] if len(extracted_text) > chunk_size else [extracted_text]
                
                for chunk_content in chunks:
                    if chunk_content.strip():
                        rag_svc.add_document(chunk_content, metadata)
                
                msg = f"✅ Tudo bem! Eu incluí o arquivo *{pending_irr.get('filename')}* no seu dossiê da viagem mesmo não parecendo ter relação direta."
                n8n = N8nService()
                n8n.enviar_resposta_usuario(request.user_id, msg, bypass_firewall=True)
                return
            
            if pending_irr and message_str.lower() in ["não", "nao", "n", "no", "descartar"]:
                user_service.clear_pending_irrelevancy(request.user_id)
                msg = "Ok, descartei o arquivo. Como posso ajudar com a viagem hoje?"
                n8n = N8nService()
                n8n.enviar_resposta_usuario(request.user_id, msg, bypass_firewall=True)
                return

            # --- Lógica de EMERGÊNCIA: Perdi meu celular / Assumir Responsável ---
            emergency_keywords = ["perdi meu celular", "perdi o celular", "assumir comando", "assumir o robô", "trocar responsável"]
            if any(kw in message_str.lower() for kw in emergency_keywords):
                active_trip_id = user_service.get_active_trip(request.user_id)
                if active_trip_id:
                    from app.services.trip_service import TripService
                    trip_svc = TripService()
                    success = trip_svc.set_primary_contact(active_trip_id, request.user_id)
                    if success:
                        resp = (
                            "🚨 *Comando de Emergência Recebido!*\n\n"
                            "Entendido. Acabei de transferir a responsabilidade da viagem para este número.\n"
                            "A partir de agora, **todas as mensagens proativas, alertas de voo e roteiros** serão enviados aqui.\n\n"
                            "Sinto muito pelo celular perdido, mas fique tranquilo(a): eu cuido de tudo por aqui agora! 🛡️✈️"
                        )
                        n8n = N8nService()
                        n8n.enviar_resposta_usuario(request.user_id, resp, bypass_firewall=True)
                        return

            if pending_link:
                msg_upper = message_str.upper()
                if msg_upper in ["SIM", "S", "YES", "OK", "CONFIRMAR"]:
                    host_id = pending_link["host_user_id"]
                    trip_id = pending_link["trip_id"]
                    dest = pending_link["destination"]
                    
                    user_service.authorize_guest(host_id, request.user_id, trip_id)
                    user_service.set_active_trip(request.user_id, trip_id)
                    user_service.clear_pending_trip_link(request.user_id)
                    
                    resp = f"✅ *Vinculação Confirmada!*\nAgora você e o Administrador compartilham o planejamento para *{dest}*."
                    n8n = N8nService()
                    n8n.enviar_resposta_usuario(request.user_id, resp, bypass_firewall=True)
                    return
                
                elif msg_upper in ["NÃO", "NAO", "N", "NO", "RECUSAR"]:
                    user_service.clear_pending_trip_link(request.user_id)
                    resp = "Entendido. Mantive seu planejamento separado e privado."
                    n8n = N8nService()
                    n8n.enviar_resposta_usuario(request.user_id, resp, bypass_firewall=True)
                    return

            if role == "admin" and message_str.lower().startswith("broadcast:"):
                broadcast_msg = message_str.split(":", 1)[1].strip()
                if not broadcast_msg:
                    resp = "❌ Por favor, digite a mensagem após o 'broadcast:'"
                else:
                    n8n = N8nService()
                    destinatarios = [uid for uid, data in user_service.users.items() if data.get("role") != "admin"]
                    results = n8n.broadcast_to_all(f"📢 *MENSAGEM DO SEVEN CONCIERGE*\n\n{broadcast_msg}", destinatarios)
                    resp = f"✅ Transmissão concluída!\nEnviado para {results['success']} usuários. Falhas: {results['failed']}."
                
                n8n = N8nService()
                n8n.enviar_resposta_usuario(request.user_id, resp)
                return

            if role == "admin" and message_str.lower().startswith("sim "):
                logger.info(f"👑 Admin {request.user_id} enviou comando de autorização explícito: {message_str}")
                guest_id = None
                parts = message_str.split(maxsplit=1)
                if len(parts) > 1: guest_id = user_service.normalize_phone(parts[1])

                if guest_id:
                    # [SMART AUTHORIZATION]
                    admin_user = user_service.get_user(request.user_id)
                    pending_requests = admin_user.get("pending_requests", {}) if admin_user else {}
                    guest_request = pending_requests.get(guest_id, {})
                    suggested_trip = guest_request.get("suggested_trip_id") if isinstance(guest_request, dict) else None
                    
                    active_trip = suggested_trip or user_service.get_active_trip(request.user_id)
                    
                    if not active_trip:
                        from app.services.trip_service import TripService
                        trip_svc = TripService()
                        admin_trips = [t for t in trip_svc.trips if t["user_id"] == request.user_id]
                        if len(admin_trips) == 1:
                            active_trip = admin_trips[0]["id"]
                            user_service.set_active_trip(request.user_id, active_trip)

                    success_trip_id = None
                    if active_trip:
                        success_trip_id = user_service.authorize_guest(request.user_id, guest_id, active_trip)
                    
                    n8n = N8nService()
                    if success_trip_id:
                        msg_admin = f"✅ Contato {guest_id} autorizado para a viagem '{success_trip_id}'!"
                        msg_guest = (
                            "🎉 *Seja muito bem-vindo ao Seven Assistant Travel - O Ápice da Consultoria de Viagens.*\n\n"
                            "O Administrador acaba de autorizar seu acesso ao **projeto de assistência mais monumental da atualidade**. Eu não sou um robô comum; sou seu **Concierge de Elite**, projetado para ser seu melhor companheiro de jornada. 🌍✈️🛡️\n\n"
                            "📋 **O QUE EU FAÇO POR VOCÊ:**\n\n"
                            "🔹 **Dossiê Digital & Auditoria:** Me envie fotos ou PDFs de suas passagens, hotéis, seguros e aluguéis de carro. Eu leio, organizo e audito tudo.\n"
                            "🔹 **Deep-Dive de Destino:** Faço pesquisas profundas sobre os lugares peculiares do seu roteiro.\n"
                            "🔹 **Consultoria & Roteiro:** Auxilio na montagem do seu itinerário e busco os melhores serviços.\n"
                            "🔹 **Radar de Ofertas:** Te aviso sobre promoções e oportunidades exclusivas.\n\n"
                            "🚀 **SUA JORNADA MONUMENTAL COMEÇA AGORA:**\n"
                            "1️⃣ *Quais são as datas exatas da sua viagem?*\n"
                            "2️⃣ *Pode me enviar seu primeiro documento ou roteiro para eu começar a trabalhar?*"
                        )
                        n8n.enviar_resposta_usuario(request.user_id, msg_admin, bypass_firewall=True)
                        n8n.enviar_resposta_usuario(guest_id, msg_guest)
                return
                    
            elif role == "admin" and message_str.lower().startswith("autorizar "):
                parts = message_str.split(maxsplit=2)
                if len(parts) >= 3:
                    guest_id = parts[1]
                    trip_id = parts[2].replace("<", "").replace(">", "").strip()
                    success = user_service.authorize_guest(request.user_id, guest_id, trip_id)
                    msg = f"✅ Contato {guest_id} autorizado para a viagem '{trip_id}'!" if success else "❌ Falha ao autorizar."
                    n8n = N8nService()
                    n8n.enviar_resposta_usuario(request.user_id, msg, bypass_firewall=True)
                return

            # --- [CENTRALIZED ACL CHECK] ---
            active_trip_id = user_service.get_active_trip(request.user_id)
            is_allowed, reason = user_service.authorize(request.user_id, active_trip_id, scope="ask")
            
            if not is_allowed:
                # Se for unauthorized completo (sem cadastro)
                if reason == "Usuário não cadastrado ou não autorizado.":
                    user_service.register_access_request(request.user_id, request.push_name)
                    n8n = N8nService()
                    admin_msg = (
                        f"🚨 *Nova Solicitação de Acesso*\n\n"
                        f"👤 Nome: {request.push_name}\n"
                        f"📱 ID: {request.user_id}\n"
                        f"💬 Mensagem: \"{request.message}\"\n\n"
                        f"Envie *sim {request.user_id}* para autorizar."
                    )
                    n8n.enviar_resposta_usuario(settings.ADMIN_WHATSAPP_NUMBER, admin_msg, bypass_firewall=True)
                    # Resposta amigável para o usuário
                    n8n.enviar_resposta_usuario(request.user_id, "👋 Olá! Eu ainda não tenho autorização para te ajudar. Já avisei o administrador e assim que ele liberar seu acesso, eu te aviso aqui! ✈️")
                    return
                else:
                    # Outros motivos de DENY (expirado, trip errada)
                    n8n = N8nService()
                    n8n.enviar_resposta_usuario(request.user_id, f"🚫 {reason}")
                    return

            # Chamada pesada da IA
            resposta_ia = agent.chat(user_input=request.message, thread_id=request.user_id)
            
            idempotency.update_status(idempotency_key, "RESPONDED", response=resposta_ia)
            
        except Exception as e:
            logger.error(f"❌ Erro no processamento background [{correlation_id}]: {e}")
            idempotency.update_status(idempotency_key, "FAILED", error_msg=str(e))
            
            try:
                n8n = N8nService()
                # Fallback mais útil com Correlation ID
                error_text = (
                    "⚠️ *Erro Interno*\n\n"
                    "Desculpe, tive uma instabilidade momentânea ao processar sua solicitação.\n"
                    f"Protocolo: `{correlation_id}`\n\n"
                    "Já registrei o problema. Se persistir, tente reenviar sua última mensagem em alguns instantes."
                )
                n8n.enviar_resposta_usuario(request.user_id, error_text, bypass_firewall=True)
            except: pass

@router.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    document_hint: Optional[str] = Form(None),
    factory: ParserFactory = Depends(get_parser_factory)
):
    """
    Upload e parse de documento de viagem
    """
    logger.info(f"📤 Recebendo documento: {file.filename}")
    
    try:
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(status_code=400, detail="Arquivo vazio")
        
        # Parse automático usando a factory
        result = factory.auto_parse(
            file_content=file_content,
            filename=file.filename,
            document_hint=document_hint
        )
        
        if not result.get("success", True):  # Se tiver success=False, falhou
            logger.warning(f"⚠️ Parse falhou: {result.get('error')}")
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "error": result.get("error", "Erro desconhecido"),
                    "document_type": result.get("document_type"),
                    "filename": file.filename
                }
            )
        
        logger.info(f"✅ Parse concluído: {result.get('document_type')}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Erro no upload: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar documento: {str(e)}"
        )
@router.post("/webhook/media")
async def media_webhook(request: MediaRequest, background_tasks: BackgroundTasks):
    """
    Endpoint para receber mídias (Base64) redirecionadas pelo n8n.
    Responde imediatamente e processa em background.
    """
    logger.info(f"📥 Recebendo mídia ({request.filename}) de {request.user_id} (ID: {request.message_id})")
    
    # --- [IDEMPOTÊNCIA] ---
    idempotency = get_idempotency()
    idempotency_key = idempotency.generate_key(request.user_id, request.message_id, media_hash=request.filename)
    
    existing_status = idempotency.check_and_register(
        idempotency_key=idempotency_key,
        chat_id=request.user_id,
        message_id=request.message_id,
        payload=request.dict()
    )

    if existing_status:
        if existing_status == "PROCESSING":
            return JSONResponse(status_code=202, content={"success": True, "message": "Já em processamento."})
        elif existing_status in ["SUCCEEDED", "RESPONDED"]:
            return JSONResponse(status_code=202, content={"success": True, "message": "Já processado."})

    background_tasks.add_task(process_media_webhook, request, idempotency_key)
    return JSONResponse(status_code=202, content={"success": True, "message": "Recebido para processamento."})

async def process_media_webhook(request: MediaRequest, idempotency_key: str):
    """Lógica de processamento de mídia em background"""
    idempotency = get_idempotency()
    correlation_id = idempotency.get_correlation_id(idempotency_key)
    
    # --- [LOCK POR USUÁRIO] ---
    lock = get_lock(request.user_id)
    async with lock:
        idempotency.update_status(idempotency_key, "PROCESSING")
        try:
            from app.services.user_service import UserService
            from app.services.document_ingestor import DocumentIngestor
            from app.services.n8n_service import N8nService
            
            user_service = UserService()
            
            # --- NOVO: FILTRO DE GRUPOS ---
            if "@g.us" in request.user_id:
                logger.info(f"👥 Grupo detectado e ignorado (Media): {request.user_id}")
                return
            
            user_data = user_service.get_user(request.user_id)
            base_role = user_data.get("role") if user_data else "unauthorized"
            
            # --- [CENTRALIZED ACL CHECK] ---
            auth = user_service.authorize(request.user_id, scope="upload")
            if not auth["allowed"]:
                reason = auth.get("reason", "Acesso negado")
                
                # Para usuários não autorizados que mandam documento, fazemos o match proativo para o admin
                if base_role == "unauthorized":
                    ingestor = DocumentIngestor()
                    data_payload = {
                        "key": {"remoteJid": f"{request.user_id}@s.whatsapp.net", "id": request.message_id},
                        "message": {"documentMessage": {"fileName": request.filename, "mimetype": request.mimetype}},
                        "base64": request.base64,
                        "message_id": request.message_id
                    }
                    
                    result = ingestor.ingest_from_webhook(data_payload, dry_run=True)
                    match = result.get("trip_match")
                    
                    suggested_trip_id = None
                    match_info = ""
                    if match:
                        suggested_trip_id = match["trip_id"]
                        match_info = f"\n\n🔍 *Match de Viagem Detectado!*\n📍 Destino: {match['destination']}\n📅 Data: {match['start_date']}"
                    
                    user_service.register_access_request(request.user_id, request.push_name, suggested_trip_id=suggested_trip_id)
                    
                    n8n = N8nService()
                    admin_msg = (
                        f"🚨 *Nova Solicitação de Acesso com Documento*\n\n"
                        f"👤 Nome: {request.push_name}\n"
                        f"📱 ID: {request.user_id}\n"
                        f"📄 Arquivo: {request.filename}{match_info}\n\n"
                        f"Envie *sim {request.user_id}* para autorizar."
                    )
                    n8n.enviar_resposta_usuario(settings.ADMIN_WHATSAPP_NUMBER, admin_msg, bypass_firewall=True)
                    n8n.enviar_resposta_usuario(request.user_id, "⚠️ Recebi seu documento, mas ainda não tenho autorização para salvá-lo. Já pedi liberação ao administrador! ✈️")
                    idempotency.update_status(idempotency_key, "RESPONDED", response="Acesso pendente admin")
                    return
                else:
                    n8n = N8nService()
                    n8n.enviar_resposta_usuario(request.user_id, f"🚫 {reason}")
                    idempotency.update_status(idempotency_key, "RESPONDED", response=f"Acesso negado: {reason}")
                    return

            normalized_uid = user_service.normalize_phone(request.user_id)
            ingestor = DocumentIngestor()
            data_payload = {
                "key": {"remoteJid": f"{normalized_uid}@s.whatsapp.net", "id": request.message_id},
                "message": {"documentMessage": {"fileName": request.filename, "mimetype": request.mimetype}},
                "base64": request.base64,
                "message_id": request.message_id
            }
            
            result = ingestor.ingest_from_webhook(data_payload)
            
            if result.get("success"):
                if result.get("status") == "conflict":
                    traveler = result.get("traveler", "Passageiro")
                    doc_type = result.get("document_type", "documento")
                    filename = result.get("filename")
                    
                    user_service.set_pending_substitution(normalized_uid, {
                        "filename": filename, 
                        "document_type": doc_type, 
                        "traveler": traveler,
                        "mimetype": result.get("mimetype"), 
                        "text": result.get("text"),
                        "drive_link": result.get("drive_link"),
                        "metadata": {
                            "filename": filename, 
                            "thread_id": normalized_uid,
                            "trip_id": user_service.get_active_trip(normalized_uid),
                            "mimetype": result.get("mimetype"), 
                            "document_type": doc_type,
                            "primary_traveler_name": traveler,
                            "segment_info": result.get("extracted_data", {}).get("segment_info"),
                            "drive_link": result.get("drive_link")
                        }
                    })
                    
                    n8n = N8nService()
                    
                    # Mensagem inteligente baseada no tipo de documento
                    if doc_type.lower() in ["passagem", "seguro"]:
                        conflict_text = f"📝 *Vi que já temos um(a) {doc_type} para {traveler} salvo(a).*"
                    else:
                        conflict_text = f"📝 *Vi que já temos um(a) {doc_type} salvo(a) para esta viagem.*"
                    
                    conflict_msg = (
                        f"{conflict_text}\n\n"
                        f"Deseja substituir pelo novo arquivo (*{filename}*)?\n"
                        f"Responda: *sim substituir* ou *não*"
                    )
                    n8n.enviar_resposta_usuario(normalized_uid, conflict_msg, bypass_firewall=True)
                    return

                # 🛡️ RELEVÂNCIA
                is_travel = result.get("is_travel_content", True)
                if not is_travel or result.get("status") == "irrelevant":
                    n8n = N8nService()
                    warning_msg = (
                        f"🤖 Analisei aqui esse documento (*{request.filename}*) e vi que ele não possui relação clara com a viagem atual.\n\n"
                        f"Tem certeza que quer incluir no seu dossiê?\n"
                        f"Responda: *sim incluir* ou *não*"
                    )
                user_service.set_pending_irrelevancy(normalized_uid, {
                    "filename": result.get("filename") or request.filename,
                    "document_type": result.get("document_type", "documento"),
                    "traveler": result.get("traveler", "viajante"),
                    "mimetype": result.get("mimetype"), 
                    "text": result.get("text"),
                    "drive_link": result.get("drive_link"),
                    "metadata": result.get("metadata", {})
                })
                n8n.enviar_resposta_usuario(normalized_uid, warning_msg, bypass_firewall=True)
                return

            # 🔑 CONFIRMAÇÃO + GAP ANALYSIS
            n8n = N8nService()
            doc_type = result.get("document_type", "documento")
            confirm_msg = (f"✅ *Documento recebido e salvo!*\n\n📄 Arquivo: {request.filename}\n📂 Tipo detectado: {doc_type}\n\n")
            
            from app.services.rag_service import RAGService
            rag = RAGService()
            user_docs = rag.list_user_documents(normalized_uid)
            
            doc_types_found = set()
            for doc_name in user_docs:
                name_lower = doc_name.lower() if doc_name else ""
                if any(w in name_lower for w in ["passagem", "ticket", "boarding", "flight", "voo"]): doc_types_found.add("passagem")
                if any(w in name_lower for w in ["hotel", "reserva", "booking", "hospedagem"]): doc_types_found.add("hotel")
                if any(w in name_lower for w in ["seguro", "insurance", "apólice"]): doc_types_found.add("seguro")
                if any(w in name_lower for w in ["carro", "car", "rental", "locação"]): doc_types_found.add("carro")
                if any(w in name_lower for w in ["roteiro", "itinerary", "guia"]): doc_types_found.add("roteiro")
                if any(w in name_lower for w in ["ingresso", "parque", "show"]): doc_types_found.add("ingresso")
            
            if doc_type:
                dt_lower = doc_type.lower()
                doc_types_found.add(dt_lower)
                if any(w in dt_lower for w in ["roteiro", "itinerary", "guia"]): doc_types_found.add("roteiro")
                if any(w in dt_lower for w in ["ingresso", "parque", "show"]): doc_types_found.add("ingresso")
            
            docs_summary = []
            if "passagem" in doc_types_found: docs_summary.append("✈️ Passagens aéreas")
            if "hotel" in doc_types_found: docs_summary.append("🏨 Reserva de hotel")
            if "seguro" in doc_types_found: docs_summary.append("🛡️ Seguro viagem")
            if "carro" in doc_types_found: docs_summary.append("🚗 Aluguel de carro")
            if "roteiro" in doc_types_found: docs_summary.append("🗺️ Roteiro / Guia")
            if "ingresso" in doc_types_found: docs_summary.append("🎟️ Ingressos/Tickets")
            
            if docs_summary:
                confirm_msg += "📂 *O que já temos salvo na sua documentação:*\n" + "\n".join([f"  ✅ {item}" for item in docs_summary])
            else:
                confirm_msg += "🎉 Este é o primeiro documento salvo da sua viagem!"
            
            n8n.enviar_resposta_usuario(normalized_uid, confirm_msg, bypass_firewall=True)
            idempotency.update_status(idempotency_key, "RESPONDED", response="Mídia processada com sucesso")
            
            trip_match = result.get("trip_match")
            if trip_match:
                host_id = trip_match["host_user_id"]
                share_msg = f"🔗 *Viagem em Grupo Detectada!*\nDeseja compartilhar seus documentos com `{host_id}`? Responda: *sim compartilhar*"
                is_first_prompt = user_service.set_pending_trip_link(normalized_uid, host_id, trip_match["trip_id"], trip_match["destination"], trip_match["start_date"])
                if is_first_prompt:
                    n8n.enviar_resposta_usuario(normalized_uid, share_msg, bypass_firewall=True)
            else:
                n8n = N8nService()
                error_msg = f"❌ *Falha ao processar:* {request.filename}\nErro: {result.get('error', 'Desconhecido')}"
                n8n.enviar_resposta_usuario(request.user_id, error_msg)
                idempotency.update_status(idempotency_key, "FAILED", error_msg=result.get("error"))
                
        except Exception as e:
            logger.error(f"❌ Erro no background media [{correlation_id}]: {e}")
            idempotency.update_status(idempotency_key, "FAILED", error_msg=str(e))

@router.post("/webhook/location")
async def location_webhook(request: LocationRequest, background_tasks: BackgroundTasks, agent: TravelAgent = Depends(get_agent)):
    """
    Endpoint para receber localização. Responde imediatamente e processa em background.
    """
    logger.info(f"📍 Localização recebida: {request.user_id}")
    background_tasks.add_task(process_location_webhook, request, agent)
    return {"success": True, "message": "Recebido"}

async def process_location_webhook(request: LocationRequest, agent: TravelAgent):
    """Lógica de geoguia proativo em background"""
    try:
        from app.services.user_service import UserService
        user_service = UserService()
        role = user_service.get_user_role(request.user_id)
        
        if role == "unauthorized": return

        from app.services.maps_service import GoogleMapsService
        maps = GoogleMapsService()
        geo_info = maps.reverse_geocode(request.latitude, request.longitude)
        
        from datetime import datetime
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        prompt = (
            f"SISTEMA: O usuário chegou em: {geo_info}. "
            f"DATA: {today_str}.\n"
            f"Analise o RAG. Se ele estiver no aeroporto ou destino hoje/amanhã, gere guia proativo.\n"
            "Responda apenas 'IGNORE' se não for relevante."
        )
        
        response = agent.chat(user_input=prompt, thread_id=request.user_id)
        
        if response and "IGNORE" not in response:
            from app.services.n8n_service import N8nService
            n8n = N8nService()
            n8n.enviar_resposta_usuario(request.user_id, response)
    except Exception as e:
        logger.error(f"❌ Erro no Geoguia background: {e}")

class DashboardActionRequest(BaseModel):
    action_type: str
    user_id: str
    details: Optional[dict] = {}

@router.post("/dashboard/action", tags=["Dashboard"])
async def dashboard_action(request: DashboardActionRequest):
    """
    Proxy endpoint for the dashboard to trigger actions on the n8n webhook
    without exposing the URL to the frontend.
    """
    webhook_url = settings.N8N_DASHBOARD_WEBHOOK_URL
    if not webhook_url:
        logger.warning("N8N_DASHBOARD_WEBHOOK_URL not configured. Unable to process dashboard action.")
        # Se não estiver configurado para testes, a gente retorna 200 pra simular sucesso pro frontend
        return {"success": True, "message": "Simulated action (Webhook URL not set)", "action": request.action_type}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json={
                    "action": request.action_type,
                    "user_id": request.user_id,
                    "details": request.details,
                    "source": "dashboard_ui"
                },
                timeout=10.0
            )
            response.raise_for_status()
            logger.info(f"Dashboard action '{request.action_type}' triggered successfully to n8n.")
            return {"success": True, "message": "Action triggered successfully", "n8n_response": response.json() if response.content else {}}
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from n8n for dashboard action: {e}")
        return JSONResponse(status_code=e.response.status_code, content={"success": False, "error": "Failed to trigger action upstream."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@router.get("/map/data", tags=["Map"])
async def get_interactive_map_data(user_id: str):
    """
    Retorna os POIs (Hoteis, Aeroportos, Eventos) extraídos do RAG do usuário.
    Usado pelo frontend (Mapbox) para plotagem visual.
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
        
    try:
        from app.services.map_service import InteractiveMapService
        map_svc = InteractiveMapService()
        locations = map_svc.get_trip_map_data(user_id)
        return {"success": True, "data": locations}
    except Exception as e:
        logger.error(f"Erro ao buscar dados do mapa: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@router.get("/documents/{filename}", tags=["Documents"])
async def get_document_file(filename: str):
    """
    Retorna o arquivo PDF ou Imagem direto do disco para visualização no iframe do Mapa.
    """
    import os
    from fastapi.responses import FileResponse
    file_path = os.path.join(settings.DOCUMENTS_PATH, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Documento não encontrado")
