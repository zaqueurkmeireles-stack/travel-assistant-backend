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

router = APIRouter()

# ============================================================
# MODELOS DE DADOS (Pydantic)
# ============================================================
class ChatRequest(BaseModel):
    user_id: str  # Número do WhatsApp (usado como thread_id na memória)
    message: str  # Mensagem do usuário

class ChatResponse(BaseModel):
    success: bool
    response: str
    user_id: str

class MediaRequest(BaseModel):
    user_id: str
    base64: str
    filename: str
    mimetype: str

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
    logger.info(f"📥 Nova mensagem de {request.user_id}: {request.message[:50]}...")
    
    try:
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
                """Confirma recebimento e analisa documentos faltantes"""
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
                    
                    # Também considerar o tipo do documento atual
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
                    
                    n8n.enviar_resposta_usuario(request.user_id, confirm_msg)
                    logger.info(f"✅ Confirmação + gap analysis enviada para {request.user_id}")
                    
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
            f"Analise os documentos dele (RAG) e, se ele estiver em um aeroporto, cidade de escala ou destino final "
            f"da viagem agendada para HOJE ou amanhã, gere uma mensagem PROATIVA de guia. "
            f"Diga onde ele está, o que ele tem que fazer a seguir (ex: imigração, pegar malas) "
            f"e ofereça as opções de economia de dados. "
            f"Se ele não estiver em local relevante para a viagem, responda apenas 'IGNORE'."
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
