"""
TravelCompanion AI - MVP Completo
Servidor FastAPI principal com estrutura modular
"""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings, setup_directories
from app.api.routes import router as api_router
from app.agents.orchestrator import TravelAgent
from app.services.n8n_service import N8nService

# Configurar logging
logger.add("logs/app.log", rotation="1 day", retention="7 days", level=settings.LOG_LEVEL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Iniciando TravelCompanion AI...")
    setup_directories()
    
    # Iniciar agendador de tarefas proativas
    try:
        from app.services.scheduler_service import SchedulerService
        scheduler = SchedulerService()
        scheduler.start()
        logger.info("📅 Agendador de tarefas proativas ativado.")
    except Exception as e:
        logger.error(f"❌ Falha ao iniciar agendador: {e}")
        
    logger.info(f"🌍 Ambiente: {settings.ENVIRONMENT}")
    yield
    
    logger.info("🛑 Encerrando TravelCompanion AI...")

app = FastAPI(
    title="TravelCompanion AI",
    description="Assistente Inteligente de Viagens - MVP Completo",
    version="1.0.0-mvp-complete",
    debug=settings.DEBUG,
    lifespan=lifespan
)
# API Routes (Injetado automaticamente)
app.include_router(api_router, prefix="/api", tags=["API"])

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar serviços
agent = TravelAgent()
n8n_service = N8nService()

# Lazily initialized to avoid circular imports or heavy startup
_ingestor = None

def get_ingestor():
    global _ingestor
    if _ingestor is None:
        from app.services.document_ingestor import DocumentIngestor
        _ingestor = DocumentIngestor()
    return _ingestor

# ... (omitted text route) ...

@app.post("/webhook/whatsapp/media", tags=["Webhooks"])
async def receive_whatsapp_media(request: Request):
    try:
        data = await request.json()
        logger.info(f"📎 Mídia (documento/imagem) recebida do n8n: {data}")
        
        # Ingestão no RAG
        result = get_ingestor().ingest_from_webhook(data)
        
        sender_number = data.get("key", {}).get("remoteJid", "").split("@")[0] or data.get("sender", "unknown")
        
        if result.get("success"):
            msg_confirmacao = f"✅ Recebi seu documento: *{result['filename']}*.\nJá memorizei os detalhes e você pode me perguntar sobre ele a qualquer momento!"
            n8n_service.enviar_resposta_usuario(sender_number, msg_confirmacao)
            
            # Se houver relatório de auditoria (gaps encontrados) → avisar proativamente
            audit_report = result.get("audit_report")
            if audit_report:
                n8n_service.enviar_resposta_usuario(sender_number, audit_report)
                logger.info(f"📢 Alerta de auditoria enviado para {sender_number}")

            # Se detectou viagem similar de outro usuário → propor vinculação
            trip_match = result.get("trip_match")
            if trip_match:
                from app.services.user_service import UserService
                user_svc = UserService()
                user_svc.set_pending_trip_link(
                    guest_id=sender_number,
                    host_user_id=trip_match["host_user_id"],
                    trip_id=trip_match["trip_id"],
                    destination=trip_match["destination"],
                    start_date=trip_match["start_date"]
                )
                msg_link = (
                    f"✈️ Ei! Vi que você vai para *{trip_match['destination']}* "
                    f"em *{trip_match['start_date']}* — "
                    f"igualzinho ao dono desta viagem! Parece que vocês estão no mesmo roteiro 😊\n\n"
                    f"Quer que eu vincule seus documentos ao planejamento da viagem para que "
                    f"todos tenham acesso às informações completas?\n\n"
                    f"Responda *SIM* para confirmar ou *NÃO* para manter separado."
                )
                n8n_service.enviar_resposta_usuario(sender_number, msg_link)
                logger.info(f"💬 Proposta de vinculação enviada para {sender_number}")
            
            return {"status": "success", "details": result}
        else:
            return {"status": "error", "message": result.get("error")}
            
    except Exception as e:
        logger.error(f"❌ Erro ao processar webhook de mídia: {e}")
        return {"status": "error", "message": str(e)}


# =================================================================
# ROTAS ORIGINAIS MANTIDAS
# =================================================================

@app.get("/")
async def root():
    return {
        "app": "TravelCompanion AI",
        "version": "1.0.0-mvp-complete",
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "features": [
            "Upload de documentos",
            "RAG com ChromaDB",
            "Notificações proativas",
            "Monitoramento de voos",
            "Geolocalização",
            "Multi-API modular",
            "Integração WhatsApp via n8n"
        ]
    }

@app.post("/webhook/whatsapp/location")
async def receive_whatsapp_location(request: Request, background_tasks: BackgroundTasks):
    """Recebe geolocalização do usuário via WhatsApp/Evolution"""
    data = await request.json()
    
    if settings.DEBUG:
        logger.debug(f"📍 Webhook localizacao recebido: {data}")
        
    try:
        sender = data.get("key", {}).get("remoteJid", "").split("@")[0] or data.get("sender", "unknown")
        # No Evolution API, a localização vem em message.locationMessage
        loc = data.get("message", {}).get("locationMessage", {})
        
        lat = loc.get("degreesLatitude")
        lng = loc.get("degreesLongitude")
        
        if lat and lng:
            from app.services.geolocation_service import GeolocationService
            geo_svc = GeolocationService()
            
            # Processar em background para não travar o webhook
            def process_arrival():
                msg = geo_svc.process_location(sender, lat, lng)
                if msg:
                    n8n_service.enviar_resposta_usuario(sender, msg)
            
            background_tasks.add_task(process_arrival)
            
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Erro ao processar localização: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "apis_configured": len([k for k in dir(settings) if k.endswith('_API_KEY')])}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )