from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from loguru import logger
import uvicorn
import os
import signal
import sys

from app.config import settings, setup_directories
from app.api.routes import router as api_router

# Lazy instances
_agent = None
_n8n_service = None
_ingestor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação (Startup/Shutdown)"""
    logger.info(f"🚀 [STARTUP] Iniciando TravelCompanion AI... (PID: {os.getpid()})")
    
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
    
    logger.info(f"🌍 [ENVIRONMENT] Modo: {settings.ENVIRONMENT} | Port: {settings.PORT} | Name: {__name__}")
    if __name__ != "__main__":
        logger.warning("⚠️ [STARTUP] O aplicativo não foi iniciado via 'python main.py'. Isso pode causar problemas de porta no Easypanel.")
    
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

# Registrar Static Files (para manifest.json, sw.js e ícones)
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Rotas PWA de Nível Superior
@app.get("/manifest.json", tags=["PWA"])
async def get_manifest():
    return FileResponse("app/static/manifest.json")

@app.get("/sw.js", tags=["PWA"])
async def get_sw():
    return FileResponse("app/static/sw.js", media_type="application/javascript")

# Setup Jinja2Templates
try:
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
except Exception as e:
    logger.error(f"Erro ao instanciar Jinja2Templates: {e}")
    # Fallback to prevent app crash if jinja is missing
    class DummyTemplates:
        def TemplateResponse(self, *args, **kwargs):
            return HTMLResponse("<h1>Jinja2 não instalado ou com erro. Verifique logs.</h1>")
    templates = DummyTemplates()

@app.get("/dashboard", response_class=HTMLResponse, tags=["UI"])
async def dashboard(request: Request, user_id: str = None):
    """Retorna o Dashboard da interface visual"""
    destination_name = "Nenhuma viagem detectada"
    
    if user_id:
        try:
            from app.services.user_service import UserService
            from app.services.trip_service import TripService
            user_svc = UserService()
            trip_svc = TripService()
            
            # Normalizar número
            clean_uid = user_svc.normalize_phone(user_id)
            active_trip_id = user_svc.get_active_trip(clean_uid)
            
            if active_trip_id:
                for trip in trip_svc.trips:
                    if trip["id"] == active_trip_id:
                        destination_name = trip.get("destination", active_trip_id)
                        break
        except Exception as e:
            logger.error(f"Erro ao buscar dados para o dashboard: {e}")

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "destination_name": destination_name,
        "user_id": user_id
    })

@app.get("/map", response_class=HTMLResponse, tags=["UI"])
async def interactive_map(request: Request):
    """Retorna o Mapa Interativo 3D (Mapbox)"""
    return templates.TemplateResponse("map.html", {
        "request": request,
        "MAPBOX_ACCESS_TOKEN": settings.MAPBOX_ACCESS_TOKEN
    })

@app.get("/test-upload", response_class=HTMLResponse, tags=["UI"])
async def test_upload_page(request: Request):
    """Página de teste para upload de documentos via Web"""
    return templates.TemplateResponse("upload_test.html", {"request": request})

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
    
    # Forçar a leitura da porta para garantir 80 em produção no Easypanel
    target_port = int(os.getenv("PORT", settings.PORT))
    logger.info(f"🚀 [LAUNCH] Iniciando Servidor na porta: {target_port}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=target_port,
        reload=settings.DEBUG,
        workers=1
    )
