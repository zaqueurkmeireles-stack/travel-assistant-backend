"""
TravelCompanion AI - MVP Completo
Servidor FastAPI principal com estrutura modular
"""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings, setup_directories
from app.api.routes import router as api_router

# Configurar logging
logger.add("logs/app.log", rotation="1 day", retention="7 days", level=settings.LOG_LEVEL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Iniciando TravelCompanion AI...")
    setup_directories()
    logger.info(f"🌍 Ambiente: {settings.ENVIRONMENT}")
    logger.info(f"🔧 Debug: {settings.DEBUG}")
    logger.info(f"🔗 Porta: {settings.PORT}")
    
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
            "Multi-API modular"
        ]
    }

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
