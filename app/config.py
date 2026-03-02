"""
Configurações da aplicação - ESTRUTURA MODULAR
Para adicionar nova API: apenas adicione a variável aqui e no .env
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path
from loguru import logger

class Settings(BaseSettings):
    # CONFIGURAÇÕES GERAIS
    ENVIRONMENT: str = "production"
    PORT: int = 8000
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    API_SECRET_KEY: str = "change-in-production"
    CORS_ORIGINS: str = "*"
    
    @property
    def cors_origins_list(self) -> list:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # ============================================================
    # INTELIGÊNCIA ARTIFICIAL
    # ============================================================
    OPENAI_API_KEY: str
    GOOGLE_GEMINI_API_KEY: Optional[str] = None
    ENABLE_DUAL_AI_CONSENSUS: bool = True
    ANTHROPIC_API_KEY: Optional[str] = None
    DUFFEL_API_KEY: Optional[str] = None
    SERP_API_KEY: Optional[str] = None
    ELEVENLABS_API_KEY: Optional[str] = None
    
    # ============================================================
    # BANCO DE DADOS (POSTGRESQL)
    # ============================================================
    DATABASE_URL: Optional[str] = None

    # ============================================================
    # WHATSAPP (DIRETO - OPCIONAL)
    # ============================================================
    WHATSAPP_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: str = "my-verify-token"
    
    # ============================================================
    # MAPAS E GEOLOCALIZAÇÃO
    # ============================================================
    GOOGLE_MAPS_API_KEY: Optional[str] = None
    
    # ============================================================
    # CLIMA
    # ============================================================
    OPENWEATHER_API_KEY: Optional[str] = None
    
    # ============================================================
    # VOOS
    # ============================================================
    AERODATABOX_API_KEY: Optional[str] = None
    AERODATABOX_API_HOST: str = "aerodatabox.p.rapidapi.com"
    
    # ============================================================
    # BUSCA E COMUNIDADES
    # ============================================================
    TAVILY_API_KEY: Optional[str] = None
    
    # ============================================================
    # N8N E AUTOMAÇÃO (NOSSO FLUXO PRINCIPAL)
    # ============================================================
    N8N_WEBHOOK_URL_OUTPUT: str = ""
    ADMIN_WHATSAPP_NUMBER: str = ""
    BOT_WHATSAPP_NUMBER: str = ""

    # ============================================================
    # EVOLUTION API (REST)
    # ============================================================
    EVOLUTION_API_URL: Optional[str] = None
    EVOLUTION_API_KEY: Optional[str] = None
    EVOLUTION_INSTANCE_NAME: str = "Seven_Assistant"
    
    # ============================================================
    # ARMAZENAMENTO
    # ============================================================
    CHROMA_DB_PATH: str = "./data/chroma_db"
    DOCUMENTS_PATH: str = "./data/documents"
    
    # ============================================================
    # GOOGLE DRIVE
    # ============================================================
    GOOGLE_DRIVE_CREDENTIALS_JSON: Optional[str] = None # JSON string or path to file
    GOOGLE_DRIVE_ROOT_FOLDER_ID: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()

def setup_directories():
    directories = [
        settings.CHROMA_DB_PATH,
        settings.DOCUMENTS_PATH,
        "./data/trips",
        "./data/cache",
        "./logs",
    ]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.debug(f"✅ Diretório: {directory}")
