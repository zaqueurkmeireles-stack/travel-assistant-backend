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
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    API_SECRET_KEY: str = "change-in-production"
    CORS_ORIGINS: str = "http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> list:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # ============================================================
    # INTELIGÊNCIA ARTIFICIAL
    # ============================================================
    OPENAI_API_KEY: str
    GOOGLE_GEMINI_API_KEY: Optional[str] = None
    ENABLE_DUAL_AI_CONSENSUS: bool = True
    
    # ============================================================
    # WHATSAPP
    # ============================================================
    WHATSAPP_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: str = "my-verify-token"
    
    # ============================================================
    # MAPAS E GEOLOCALIZAÇÃO
    # ============================================================
    GOOGLE_MAPS_API_KEY: str
    
    # ============================================================
    # CLIMA
    # ============================================================
    OPENWEATHER_API_KEY: str
    
    # ============================================================
    # VOOS
    # ============================================================
    AERODATABOX_API_KEY: Optional[str] = None
    AERODATABOX_API_HOST: str = "aerodatabox.p.rapidapi.com"
    
    # ============================================================
    # BUSCA E COMUNIDADES
    # ============================================================
    TAVILY_API_KEY: Optional[str] = None
    REDDIT_CLIENT_ID: Optional[str] = None
    REDDIT_CLIENT_SECRET: Optional[str] = None
    REDDIT_USER_AGENT: str = "travel_assistant:v1.0"
    
    # ============================================================
    # LOCAIS E RESTAURANTES
    # ============================================================
    FOURSQUARE_API_KEY: Optional[str] = None
    
    # ============================================================
    # SÍNTESE DE VOZ
    # ============================================================
    ELEVENLABS_API_KEY: Optional[str] = None
    
    # ============================================================
    # N8N E AUTOMAÇÃO
    # ============================================================
    N8N_API_KEY: Optional[str] = None
    N8N_WEBHOOK_URL: Optional[str] = None
    
    # ============================================================
    # ARMAZENAMENTO
    # ============================================================
    CHROMA_DB_PATH: str = "./data/chroma_db"
    DOCUMENTS_PATH: str = "./data/documents"
    
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
