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

# Health Checks (Easypanel)
@app.get("/health", tags=["System"])
async def health_check_system():
    return {"status": "ok", "service": "TravelCompanion AI"}

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


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )