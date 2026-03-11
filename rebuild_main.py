import os

file_path = "main.py"

content = """import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from app.api import routes, shield
from app.services.scheduler_service import SchedulerService
from app.config import settings

# 🚀 INICIALIZAÇÃO DO ANTIGRAVITY
app = FastAPI(
    title="Antigravity Travel Assistant",
    description="Sistema de Orquestração de Viagens Resiliente",
    version="2.0.0"
)

# 🛡️ CONFIGURAÇÃO DE CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔗 ACOPLAMENTO DE ROTAS
app.include_router(routes.router)
app.include_router(shield.router, prefix="/shield", tags=["Shield"])

# 📅 EVENTO DE STARTUP (O Coração Proativo)
@app.on_event("startup")
async def startup_event():
    logger.info(f"🚀 [STARTUP] Iniciando Antigravity AI... (PID: {os.getpid()})")
    try:
        # Liga o motor de monitoramento de voos e eventos
        scheduler = SchedulerService()
        scheduler.start()
        app.state.scheduler = scheduler
        logger.info("📅 [SCHEDULER] Agendador ativado com sucesso.")
    except Exception as e:
        logger.error(f"❌ [SCHEDULER] Falha ao iniciar: {e}")

@app.get("/")
async def root():
    return {"status": "online", "system": "Antigravity", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    logger.info("📡 [LAUNCH] Iniciando Servidor Antigravity na porta 80...")
    uvicorn.run(app, host="0.0.0.0", port=80)
"""

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("✨ main.py RECONSTRUÍDO! A sintaxe está limpa e o motor pronto.")
