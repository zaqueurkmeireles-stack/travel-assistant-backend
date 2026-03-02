from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import uvicorn
import os

from app.config import settings, setup_directories
from app.api.routes import router as api_router

# Lazy instances
_agent = None
_n8n_service = None
_ingestor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação (Startup/Shutdown)"""
    logger.info("🚀 [STARTUP] Iniciando TravelCompanion AI...")
    
    # 1. Preparar diretórios
    setup_directories()
    
    # 2. Iniciar agendador de tarefas proativas
    try:
        from app.services.scheduler_service import SchedulerService
        app.state.scheduler = SchedulerService()
        app.state.scheduler.start()
        logger.info("📅 [SCHEDULER] Agendador ativado com sucesso.")
    except Exception as e:
        logger.error(f"❌ [SCHEDULER] Falha ao iniciar: {e}")
    
    logger.info(f"🌍 [ENVIRONMENT] Modo: {settings.ENVIRONMENT} | Port: {settings.PORT}")
    
    yield
    
    logger.info("🛑 [SHUTDOWN] Encerrando TravelCompanion AI...")

# Inicialização do App FastAPI
app = FastAPI(
    title="TravelCompanion AI",
    description="Assistente Concierge de Viagens de Elite",
    version="1.1.0",
    debug=settings.DEBUG,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check Unificado (Padrão para Easypanel / Portainer)
@app.get("/", tags=["System"])
@app.get("/health", tags=["System"])
@app.get("/api/health", tags=["System"]) # Adicionado para compatibilidade total
async def health_check():
    """Endpoint de vitalidade do serviço"""
    logger.info("📡 [HEALTHCHECK] Requisição recebida com sucesso.")
    return {
        "status": "online",
        "service": "Seven Assistant Travel",
        "version": "1.1.0",
        "environment": settings.ENVIRONMENT
    }

# Registrar Rotas da API
app.include_router(api_router, prefix="/api", tags=["API"])

# Dependências Globais / Inicialização Tardia
def get_agent():
    global _agent
    if _agent is None:
        from app.agents.orchestrator import TravelAgent
        _agent = TravelAgent()
    return _agent

def get_n8n():
    global _n8n_service
    if _n8n_service is None:
        from app.services.n8n_service import N8nService
        _n8n_service = N8nService()
    return _n8n_service

if __name__ == "__main__":
    # Garante que o diretório de logs existe antes de configurar o logger de arquivo
    if not os.path.exists("./logs"):
        os.makedirs("./logs")
    
    logger.add("logs/app.log", rotation="1 day", retention="7 days", level=settings.LOG_LEVEL)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 # Um único worker por container para evitar lock de arquivos (ChromaDB)
    )
