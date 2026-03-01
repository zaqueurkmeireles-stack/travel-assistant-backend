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

router = APIRouter()

# ============================================================
# MODELOS DE DADOS (Pydantic)
# ============================================================
class ChatRequest(BaseModel):
    user_id: str  # Número do WhatsApp (usado como thread_id na memória)
    message: str  # Mensagem do usuário
    push_name: Optional[str] = "Desconhecido"

class ChatResponse(BaseModel):
    success: bool
    response: str
    user_id: str

class MediaRequest(BaseModel):
    user_id: str
    base64: str
    filename: str
    mimetype: str
    push_name: Optional[str] = "Desconhecido"

class LocationRequest(BaseModel):
    user_id: str
    latitude: float
    longitude: float
    address: Optional[str] = None

# ============================================================
# GERENCIAMENTO DE DEPENDÊNCIAS (Singletons para Performance)
# ============================================================
_agent = None
_parser_factory = None

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

@router.get("/health")
async def health_check():
    """Health check - Verifica se a API está funcionando"""
    return {
        "status": "healthy",
        "service": "TravelCompanion AI API"
    }

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    agent: TravelAgent = Depends(get_agent)
):
    """
    Endpoint principal de Chat (Webhook para n8n/WhatsApp)
    Recebe a mensagem, processa no LangGraph, devolve a resposta ao WhatsApp via N8nService
    e retorna JSON para o n8n.
    """
    if not request.user_id or request.user_id.strip() == "":
        logger.error("❌ Erro: Request recebido com user_id vazio. Verifique o mapeamento no n8n.")
        return ChatResponse(
            success=True,
            response="",
            user_id="desconhecido"
        )
    
    try:
        from app.services.user_service import UserService
        user_service = UserService()
        
        # 🛡️ NORMALIZAÇÃO IMEDIATA (evita erros de prefixo 9 extra)
        logger.info(f"📡 [INCOMING] Recebido de n8n: {request.user_id}")
        original_user_id = request.user_id
        request.user_id = user_service.normalize_phone(request.user_id)
        
        if not request.user_id:
            return ChatResponse(
                success=True,
                response="",
                user_id="invalid"
            )

        logger.info(f"📥 [RAW] Mensagem de {request.user_id}: {request.message[:50]}...")
            
        logger.info(f"👤 [NORMALIZADO] {request.user_id}")
        
        # 🛑 PREVENÇÃO EVOLUTION API: Ignorar mensagens vazias (Eventos de leitura, status, delivery receipts)
        if not request.message or not request.message.strip():
            return ChatResponse(success=True, response="", user_id=request.user_id)

        # 🛑 PREVENÇÃO DE LOOP INFINITO: Ignorar mensagens enviadas pelo próprio bot
        bot_number = user_service.normalize_phone(getattr(settings, "BOT_WHATSAPP_NUMBER", ""))
        if bot_number and request.user_id == bot_number:
            logger.info("🛑 Mensagem ignorada: O remetente é o próprio bot (Prevenção de loop infinito).")
            return ChatResponse(success=True, response="", user_id=request.user_id)
            
        # [DIAGNOSTICO] Logar todos os contatos em um arquivo persistente para identificar IDs
        try:
            with open("data/contact_history.txt", "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()} | ID: {request.user_id} | MSG: {request.message[:50]}...\n")
        except:
            pass

        # 🛑 PREVENÇÃO DE ECO (FORK BOMB): A Evolution API pode enviar as respostas do próprio bot de volta.
        message_str = request.message.strip()
        bot_signatures = [
            "BEM-VINDO AO SEVEN ASSISTANT TRAVEL",
            "Pedido de Acesso!",
            "seven assistant",
            "Aqui estão os detalhes da sua viagem",
            "Aqui estão os documentos de viagem",
            "Aqui estão os documentos salvos",
            "Não vejo novos bilhetes de passagem",
            "✅ Documento recebido e salvo!",
            "📋 Checklist de documentos:",
            "🎉 Todos os documentos essenciais já estão salvos",
            "🔗 Viagem em Grupo Detectada!",
            "📋 *Checklist de documentos:*",
            "Sucesso no n8n para",
            "Resumo da Comunidade:",
            "Como posso ajudar com a viagem hoje?"
        ]
        if any(sig.lower() in message_str.lower() for sig in bot_signatures) and len(message_str) > 20:
            logger.info(f"🛑 Mensagem ignorada: Detectado ECHO ({message_str[:30]}...)")
            return ChatResponse(success=True, response="", user_id=request.user_id)
        
        # --- NOVO: FILTRO DE GRUPOS (SEGURANÇA EXTRA) ---
        if "@g.us" in request.user_id:
            logger.info(f"👥 Grupo detectado e ignorado: {request.user_id}")
            return ChatResponse(success=True, response="", user_id=request.user_id)
        
        role = user_service.get_user_role(request.user_id)
        # Garantir que o comando "autorizar" funcione sempre
        message_clean = request.message.strip()
        
        # --- NOVO: Lógica de Confirmação de Vinculação Automática (SIM/NÃO) ---
        pending_link = user_service.get_pending_trip_link(request.user_id)
        if pending_link:
            msg_upper = message_clean.upper()
            if msg_upper in ["SIM", "S", "YES", "OK", "CONFIRMAR"]:
                host_id = pending_link["host_user_id"]
                trip_id = pending_link["trip_id"]
                dest = pending_link["destination"]
                
                # Efetiva a vinculação e autorização
                user_service.authorize_guest(host_id, request.user_id, trip_id)
                user_service.set_active_trip(request.user_id, trip_id)
                user_service.clear_pending_trip_link(request.user_id)
                
                resp = f"✅ *Vinculação Confirmada!*\nAgora você e o Administrador compartilham o planejamento para *{dest}*.\n\nQualquer documento que um de vocês enviar será memorizado para ambos. Como posso ajudar com a viagem hoje?"
                n8n = N8nService()
                background_tasks.add_task(n8n.enviar_resposta_usuario, request.user_id, resp)
                return ChatResponse(success=True, response=resp, user_id=request.user_id)
            
            elif msg_upper in ["NÃO", "NAO", "N", "NO", "RECUSAR"]:
                user_service.clear_pending_trip_link(request.user_id)
                resp = "Entendido. Mantive seu planejamento separado e privado. Para qualquer dúvida, estou à disposição!"
                n8n = N8nService()
                background_tasks.add_task(n8n.enviar_resposta_usuario, request.user_id, resp)
                return ChatResponse(success=True, response=resp, user_id=request.user_id)
        # --------------------------------------------------------------------

        if role == "admin" and message_clean.lower().startswith("broadcast:"):
            broadcast_msg = message_clean.split(":", 1)[1].strip()
            if not broadcast_msg:
                resp = "❌ Por favor, digite a mensagem após o 'broadcast:'"
            else:
                n8n = N8nService()
                destinatarios = [uid for uid, data in user_service.users.items() if data.get("role") != "admin"]
                results = n8n.broadcast_to_all(f"📢 *MENSAGEM DO SEVEN CONCIERGE*\n\n{broadcast_msg}", destinatarios)
                resp = f"✅ Transmissão concluída!\nEnviado para {results['success']} usuários. Falhas: {results['failed']}."
            
            n8n = N8nService()
            background_tasks.add_task(n8n.enviar_resposta_usuario, request.user_id, resp)
            return ChatResponse(success=True, response=resp, user_id=request.user_id)

        if role == "admin" and (message_clean.lower() in ["ok", "sim"] or message_clean.lower().startswith("sim ")):
            logger.info(f"👑 Admin {request.user_id} enviou comando de autorização: {message_clean}")
            if message_clean.lower() in ["ok", "sim"]:
                # Pega o último pedido pendente
                admin_user = user_service.get_user(request.user_id)
                pending_requests = admin_user.get("pending_requests", {}) if admin_user else {}
                
                if not pending_requests:
                    # Tentar fallback: Procura por QUALQUER usuário 'unauthorized' no DB nas últimas 2h
                    logger.warning("⚠️ Sem pending_requests explícitos. Buscando usuários unauthorized recentes...")
                    unauthorized_users = [uid for uid, data in user_service.users.items() if data.get("role") == "unauthorized"]
                    if unauthorized_users:
                        guest_id = unauthorized_users[-1] # Pega o último
                        logger.info(f"🔄 Fallback: Autorizando último unauthorized encontrado: {guest_id}")
                    else:
                        msg = "❌ Não há pedidos de acesso pendentes ou usuários não autorizados recentes."
                        n8n = N8nService()
                        background_tasks.add_task(n8n.enviar_resposta_usuario, request.user_id, msg)
                        return ChatResponse(success=True, response=msg, user_id=request.user_id)
                else:
                    # Pega o pedido mais recente
                    guest_id = sorted(pending_requests.items(), key=lambda x: x[1], reverse=True)[0][0]
            else:
                parts = message_clean.split(maxsplit=1)
                guest_id = user_service.normalize_phone(parts[1])

            active_trip = user_service.get_active_trip(request.user_id)
            logger.info(f"⚙️ Tentando autorizar {guest_id} para a trip {active_trip}")
            
            # 🛡️ FALLBACK: Se o admin não tem viagem ativa setada, mas existe uma única viagem registrada para ele
            if not active_trip:
                from app.services.trip_service import TripService
                trip_svc = TripService()
                admin_trips = [t for t in trip_svc.trips if t["user_id"] == request.user_id]
                if len(admin_trips) == 1:
                    active_trip = admin_trips[0]["id"]
                    user_service.set_active_trip(request.user_id, active_trip)
                    logger.info(f"🔄 Fallback: Ativando única viagem encontrada '{active_trip}' para o admin.")

            success_trip_id = None
            if active_trip:
                success_trip_id = user_service.authorize_guest(request.user_id, guest_id, active_trip)
            
            if success_trip_id:
                msg_admin = f"✅ Contato {guest_id} autorizado para a viagem '{success_trip_id}'!"
                msg_guest = (
                    f"🎉 Olá! O Administrador liberou seu acesso. Eu sou o *Seven Assistant Travel*. "
                    f"Posso te ajudar a organizar roteiros, passagens e reservas, além de dar dicas proativas durante sua viagem!\n\n"
                    f"Para começar, me envie o seu *roteiro* (mesmo que seja apenas um rascunho com datas e local) para que eu possa planejar tudo pra você!"
                )
                
                n8n = N8nService()
                background_tasks.add_task(n8n.enviar_resposta_usuario, guest_id, msg_guest)
                return ChatResponse(success=True, response=msg_admin, user_id=request.user_id)
            else:
                msg = "❌ Falha ao autorizar. Você tem uma Viagem Ativa cadastrada ou documento enviado?"
                n8n = N8nService()
                background_tasks.add_task(n8n.enviar_resposta_usuario, request.user_id, msg)
                return ChatResponse(success=True, response=msg, user_id=request.user_id)
                
        # Manter compatibilidade do comando antigo completo
        elif role == "admin" and message_clean.lower().startswith("autorizar "):
            parts = message_clean.split(maxsplit=2) # Split apenas nos primeiros 2 espaços
            if len(parts) >= 3:
                guest_id = parts[1]
                trip_id = parts[2].replace("<", "").replace(">", "").strip()
                success = user_service.authorize_guest(request.user_id, guest_id, trip_id)
                msg = f"✅ Contato {guest_id} autorizado para a viagem '{trip_id}'!" if success else "❌ Falha ao autorizar."
                
                n8n = N8nService()
                # 🛑 REMOVIDO: Envio via background task redundante
                # background_tasks.add_task(n8n.enviar_resposta_usuario, request.user_id, msg)
                return ChatResponse(success=True, response=msg, user_id=request.user_id)
            else:
                msg = "⚠️ Formato incorreto. Use: sim <numero> ou autorizar <numero> <viagem>"
                n8n = N8nService()
                # background_tasks.add_task(n8n.enviar_resposta_usuario, request.user_id, msg)
                return ChatResponse(success=True, response=msg, user_id=request.user_id)

        if role == "unauthorized":
            # [REGISTRO] Salva na fila de espera do Admin com o Nome
            should_notify = user_service.register_access_request(request.user_id, request.push_name)
            
            if should_notify:
                n8n = N8nService()
                admin_msg = (
                    f"🚨 *Nova Solicitação de Acesso*\n\n"
                    f"👤 Nome: {request.push_name}\n"
                    f"📱 ID: {request.user_id}\n"
                    f"💬 Mensagem: \"{request.message}\"\n\n"
                    f"Envie *sim {request.user_id}* para autorizar."
                )
                background_tasks.add_task(n8n.enviar_resposta_usuario, settings.ADMIN_WHATSAPP_NUMBER, admin_msg)
                logger.info(f"📢 Admin notificado sobre acesso pendente: {request.user_id}")

            # [SILENT MODE] O robô JAMAIS deve responder ao usuário não autorizado.
            return ChatResponse(success=True, response="", user_id=request.user_id)

        # Passamos o user_id como thread_id para o LangGraph manter a memória da conversa
        resposta_ia = agent.chat(user_input=request.message, thread_id=request.user_id)
        
        # 🔑 FECHANDO O LOOP: envia a resposta de volta ao WhatsApp via n8n em background
        # Isso evita travar o webhook enquanto o n8n processa o envio
        if resposta_ia:
            n8n = N8nService()
            background_tasks.add_task(
                n8n.enviar_resposta_usuario,
                request.user_id,
                resposta_ia
            )
            logger.info(f"✅ Resposta agendada para envio ao WhatsApp ({request.user_id})")
        
        return ChatResponse(
            success=True,
            response=resposta_ia,
            user_id=request.user_id
        )
    except Exception as e:
        logger.error(f"❌ Erro ao processar chat: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno no processamento do agente: {str(e)}"
        )

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
    Após indexar o documento no RAG, envia confirmação ao usuário via WhatsApp
    e realiza gap analysis para verificar documentos faltantes.
    """
    logger.info(f"📥 Recebendo mídia ({request.filename}) de {request.user_id}")
    
    try:
        from app.services.user_service import UserService
        user_service = UserService()
        # --- NOVO: FILTRO DE GRUPOS (SEGURANÇA EXTRA) ---
        if "@g.us" in request.user_id:
            logger.info(f"👥 Grupo detectado e ignorado (Media): {request.user_id}")
            return JSONResponse(status_code=202, content={"success": True, "message": "Ignorado (Grupo)"})

        role = user_service.get_user_role(request.user_id)
        
        if role == "unauthorized":
            logger.info(f"⏳ Processando mídia (unauthorized) para preview do Admin: {request.user_id}")
            # [SILENT MODE] Notifica apenas o Admin, NUNCA responde ao usuário.
            n8n = N8nService()
            admin_msg = (
                f"🚨 *Nova Solicitação de Acesso com Documento*\n\n"
                f"👤 Nome: {request.push_name}\n"
                f"📱 ID: {request.user_id}\n"
                f"📄 Arquivo: {request.filename}\n\n"
                f"Envie *sim {request.user_id}* para autorizar e processar o documento."
            )
            background_tasks.add_task(n8n.enviar_resposta_usuario, settings.ADMIN_WHATSAPP_NUMBER, admin_msg)
            
            return JSONResponse(status_code=202, content={
                "success": True, 
                "message": "Enviado para aprovação do Administrador."
            })

        request.user_id = user_service.normalize_phone(request.user_id)
        ingestor = DocumentIngestor()
        # Adaptar o payload para o formato esperado pelo ingestor
        data_payload = {
            "key": {"remoteJid": f"{request.user_id}@s.whatsapp.net"},
            "message": {
                "documentMessage": {
                    "fileName": request.filename,
                    "mimetype": request.mimetype
                }
            },
            "base64": request.base64
        }
        
        result = ingestor.ingest_from_webhook(data_payload)
        
        if result.get("success"):
            # 🔑 ENVIAR CONFIRMAÇÃO + GAP ANALYSIS ao usuário via WhatsApp
            doc_type = result.get("document_type", "documento")
            preview = result.get("text_preview", "")
            
            def send_confirmation_and_gap_analysis():
                """Confirma recebimento, analisa documentos faltantes e oferece compartilhamento"""
                try:
                    n8n = N8nService()
                    
                    # 1. Mensagem de confirmação
                    confirm_msg = (
                        f"✅ *Documento recebido e salvo!*\n\n"
                        f"📄 Arquivo: {request.filename}\n"
                        f"📂 Tipo detectado: {doc_type}\n\n"
                    )
                    
                    # 2. Gap Analysis - verificar documentos faltantes
                    from app.services.rag_service import RAGService
                    rag = RAGService()
                    user_docs = rag.list_user_documents(request.user_id)
                    
                    doc_types_found = set()
                    for doc_name in user_docs:
                        name_lower = doc_name.lower() if doc_name else ""
                        if any(w in name_lower for w in ["passagem", "ticket", "boarding", "flight", "voo"]):
                            doc_types_found.add("passagem")
                        if any(w in name_lower for w in ["hotel", "reserva", "booking", "hospedagem"]):
                            doc_types_found.add("hotel")
                        if any(w in name_lower for w in ["seguro", "insurance", "apólice", "apolice"]):
                            doc_types_found.add("seguro")
                        if any(w in name_lower for w in ["carro", "car", "rental", "locação", "locadora"]):
                            doc_types_found.add("carro")
                    
                    if doc_type:
                        doc_types_found.add(doc_type.lower())
                    
                    missing = []
                    checklist_items = {
                        "passagem": "✈️ Passagens aéreas / Boarding pass",
                        "hotel": "🏨 Reserva de hotel / hospedagem", 
                        "seguro": "🛡️ Seguro viagem / apólice",
                    }
                    
                    for key, label in checklist_items.items():
                        if key not in doc_types_found:
                            missing.append(label)
                    
                    if missing:
                        confirm_msg += (
                            "📋 *Checklist de documentos:*\n"
                            + "\n".join([f"  ⬜ {item}" for item in missing])
                            + "\n\n💡 Envie os documentos faltantes aqui no chat que eu salvo tudo pra você!"
                        )
                    else:
                        confirm_msg += "🎉 Todos os documentos essenciais já estão salvos! Estou pronto pra te guiar!"
                    
                    # [NOVO] Contador de documentos totais no RAG
                    total_docs = len(user_docs)
                    confirm_msg += f"\n\n📊 *Status do RAG:* {total_docs} documentos salvos e indexados."
                    
                    n8n.enviar_resposta_usuario(request.user_id, confirm_msg)
                    logger.info(f"✅ Confirmação + gap analysis enviada para {request.user_id}")
                    
                    # 3. [NOVO] Oferta de Compartilhamento de Viagem (Shared RAG)
                    trip_match = result.get("trip_match")
                    if trip_match:
                        host_id = trip_match["host_user_id"]
                        dest = trip_match["destination"]
                        date = trip_match["start_date"]
                        
                        share_msg = (
                            f"🔗 *Viagem em Grupo Detectada!*\\n"
                            f"Notei que o usuário `{host_id}` também tem uma viagem para *{dest}* em *{date}*.\\n\\n"
                            "Deseja compartilhar seus documentos com ele para que eu possa guiar vocês dois juntos?\\n"
                            "Responda: *sim compartilhar*"
                        )
                        # Salva a intenção pendente para o comando simplificado
                        user_service.set_pending_trip_link(
                            guest_id=request.user_id,
                            host_user_id=host_id,
                            trip_id=trip_match["trip_id"],
                            destination=dest,
                            start_date=date
                        )
                        n8n.enviar_resposta_usuario(request.user_id, share_msg)
                        logger.info(f"🔗 Oferta de compartilhamento enviada para {request.user_id}")
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao enviar confirmação: {e}")
            
            background_tasks.add_task(send_confirmation_and_gap_analysis)
            
            return {"success": True, "message": f"Documento {request.filename} indexado com sucesso!"}
        else:
            return JSONResponse(status_code=422, content=result)
            
    except Exception as e:
        logger.error(f"❌ Erro no webhook de mídia: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@router.post("/webhook/location")
async def location_webhook(request: LocationRequest, agent: TravelAgent = Depends(get_agent)):
    """
    Endpoint para receber localização e disparar guia proativo automático
    """
    logger.info(f"📍 Geolocalização Proativa: {request.user_id} em {request.latitude}, {request.longitude}")
    
    try:
        from app.services.user_service import UserService
        user_service = UserService()
        role = user_service.get_user_role(request.user_id)
        
        if role == "unauthorized":
            logger.warning(f"🚫 Localização ignorada. Usuário não autorizado: {request.user_id}")
            return {"success": False, "message": "Não autorizado"}

        # 1. Obter contexto Geográfico (Cidade/País/POI)
        from app.services.maps_service import GoogleMapsService
        maps = GoogleMapsService()
        geo_info = maps.reverse_geocode(request.latitude, request.longitude)
        
        from datetime import datetime
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # 2. Chamar a IA para decidir se deve enviar um 'Welcome' ou 'Guide' proativo
        # Passamos a localização como um evento de sistema
        prompt = (
            f"SISTEMA: O usuário acabou de chegar em: {geo_info}. "
            f"Coordenadas: {request.latitude}, {request.longitude}. "
            f"DATA DE HOJE: {today_str}.\n"
            f"Analise os documentos dele (RAG) e, se ele estiver em um aeroporto (partida ou escala) ou destino final "
            f"da viagem agendada para HOJE ou amanhã, gere uma mensagem PROATIVA de guia.\n\n"
            "DIRETRIZES:\n"
            "1. Diga onde ele está e o que ele tem que fazer a seguir (ex: 'Bem-vindo! Você chegou ao Terminal 2').\n"
            "2. Se ele estiver chegando no destino, mencione Locadora de Carros ou Hotel (se houver no RAG).\n"
            "3. Você DEVE oferecer o link de navegação usando a ferramenta 'provide_visual_navigation_map' "
            "para o próximo ponto lógico (ex: Hertz Rental, Uber area, ou Hotel).\n"
            "4. Mencione explicitamente que ele pode salvar o mapa para USO OFFLINE e economizar dados.\n"
            "5. Se ele não estiver em local relevante, responda apenas 'IGNORE'."
        )
        
        response = agent.chat(user_input=prompt, thread_id=request.user_id)
        
        if response and "IGNORE" not in response:
            from app.services.n8n_service import N8nService
            n8n = N8nService()
            n8n.enviar_resposta_usuario(request.user_id, response)
            return {"success": True, "proactive_sent": True}
            
        return {"success": True, "proactive_sent": False}
        
    except Exception as e:
        logger.error(f"❌ Erro no Geoguia Proativo: {e}")
        return {"success": False, "error": str(e)}
