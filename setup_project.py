"""
TravelCompanion AI - Setup Master 100% Automático
Executa: python setup_project.py
Cria TODA a estrutura do MVP Completo automaticamente
"""

import os
from pathlib import Path

# ============================================================
# ESTRUTURA DE PASTAS
# ============================================================

FOLDERS = [
    "app",
    "app/models",
    "app/database",
    "app/parsers",
    "app/services",
    "app/agents",
    "app/api",
    "app/utils",
    "data/chroma_db",
    "data/documents",
    "data/trips",
    "data/cache",
    "logs",
    "tests",
]

# ============================================================
# CONTEÚDO DOS ARQUIVOS
# ============================================================

FILES = {}

# ============================================================
# REQUIREMENTS.TXT
# ============================================================
FILES["requirements.txt"] = """# ============================================================
# TRAVELCOMPANION AI - MVP COMPLETO - DEPENDÊNCIAS
# ============================================================

# Framework Web
fastapi==0.115.5
uvicorn[standard]==0.32.1
pydantic==2.10.3
pydantic-settings==2.6.1
python-multipart==0.0.20

# LangChain e LangGraph
langchain==0.3.13
langchain-openai==0.2.14
langchain-google-genai==2.0.8
langgraph==0.2.59
langchain-community==0.3.13

# OpenAI
openai==1.59.5

# RAG e Embeddings
chromadb==0.5.23
sentence-transformers==3.3.1

# Processamento de Documentos
pypdf2==3.0.1
python-docx==1.1.2
pillow==11.0.0
pytesseract==0.3.13

# Agendamento de Tarefas
apscheduler==3.10.4

# Parsing de Datas
dateparser==1.2.0

# Persistência
sqlalchemy==2.0.36

# Requests
requests==2.32.5
httpx==0.28.1

# Ambiente
python-dotenv==1.0.1

# Logging
loguru==0.7.3

# Utilidades
python-dateutil==2.9.0.post0
typing-extensions==4.12.2
"""

# ============================================================
# APP/CONFIG.PY (MODULAR PARA NOVAS APIs)
# ============================================================
FILES["app/config.py"] = '''"""
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
    N8N_WEBHOOK_URL_OUTPUT: Optional[str] = None
    
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
'''

# ============================================================
# APP/__INIT__.PY
# ============================================================
FILES["app/__init__.py"] = '''"""TravelCompanion AI - MVP Completo"""
__version__ = "1.0.0-mvp-complete"
__author__ = "TravelCompanion Team"
'''

# ============================================================
# MODELOS
# ============================================================
FILES["app/models/__init__.py"] = '''"""Modelos de dados"""
from .trip import Trip
from .document import TravelDocument
from .flight import Flight
from .hotel import Hotel
from .notification import Notification

__all__ = ["Trip", "TravelDocument", "Flight", "Hotel", "Notification"]
'''

FILES["app/models/trip.py"] = '''"""Modelo de viagem"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Trip(BaseModel):
    """Modelo de dados de uma viagem"""
    id: str = Field(..., description="ID único da viagem")
    user_id: str = Field(..., description="ID do usuário")
    destination: str = Field(..., description="Destino principal")
    start_date: datetime = Field(..., description="Data de início")
    end_date: datetime = Field(..., description="Data de término")
    status: str = Field(default="planning", description="Status da viagem")
    budget: Optional[float] = Field(None, description="Orçamento inicial")
    current_balance: Optional[float] = Field(None, description="Saldo atual dinâmico e disponível")
    drawdown: float = Field(default=0.0, description="Gastos e saques acumulados")
    travelers_count: int = Field(default=1, description="Número de viajantes")
'''

FILES["app/models/document.py"] = '''"""Modelo de documento de viagem"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TravelDocument(BaseModel):
    """Modelo de documento de viagem"""
    id: str = Field(..., description="ID único do documento")
    trip_id: str = Field(..., description="ID da viagem")
    document_type: str = Field(..., description="Tipo: passport, visa, ticket, hotel, insurance")
    file_path: str = Field(..., description="Caminho do arquivo")
    extracted_text: Optional[str] = Field(None, description="Texto extraído")
    uploaded_at: datetime = Field(default_factory=datetime.now, description="Data de upload")
'''

FILES["app/models/flight.py"] = '''"""Modelo de voo"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Flight(BaseModel):
    """Modelo de dados de voo"""
    flight_number: str = Field(..., description="Número do voo")
    airline: str = Field(..., description="Companhia aérea")
    departure_airport: str = Field(..., description="Aeroporto de origem")
    arrival_airport: str = Field(..., description="Aeroporto de destino")
    departure_time: datetime = Field(..., description="Horário de partida")
    arrival_time: datetime = Field(..., description="Horário de chegada")
    gate: Optional[str] = Field(None, description="Portão de embarque")
    status: str = Field(default="scheduled", description="Status do voo")
'''

FILES["app/models/hotel.py"] = '''"""Modelo de hotel"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Hotel(BaseModel):
    """Modelo de reserva de hotel"""
    name: str = Field(..., description="Nome do hotel")
    address: str = Field(..., description="Endereço")
    check_in_date: datetime = Field(..., description="Data de check-in")
    check_out_date: datetime = Field(..., description="Data de check-out")
    reservation_code: str = Field(..., description="Código de reserva")
    contact_phone: Optional[str] = Field(None, description="Telefone do hotel")
'''

FILES["app/models/notification.py"] = '''"""Modelo de notificação"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Notification(BaseModel):
    """Modelo de notificação proativa"""
    id: str = Field(..., description="ID único")
    user_id: str = Field(..., description="ID do usuário")
    trip_id: str = Field(..., description="ID da viagem")
    message: str = Field(..., description="Mensagem da notificação")
    notification_type: str = Field(..., description="Tipo: reminder, alert, info")
    scheduled_time: datetime = Field(..., description="Horário agendado")
    sent: bool = Field(default=False, description="Se foi enviada")
    sent_at: Optional[datetime] = Field(None, description="Quando foi enviada")
'''

# ============================================================
# INJEÇÃO AUTOMÁTICA DE __INIT__.PY
# ============================================================
for folder in ["app/database", "app/parsers", "app/services", "app/agents", "app/api", "app/utils", "tests"]:
    if f"{folder}/__init__.py" not in FILES:
        FILES[f"{folder}/__init__.py"] = '"""Módulo gerado automaticamente"""\n'


# ============================================================
# EXECUÇÃO DO SETUP
# ============================================================
def create_project_structure():
    """Cria toda a estrutura do projeto"""
    
    print("=" * 60)
    print("🚀 TRAVELCOMPANION AI - SETUP SEGURO")
    print("=" * 60)
    print()
    
    # Criar pastas
    print("📁 Criando estrutura de pastas...")
    for folder in FOLDERS:
        Path(folder).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {folder}")
    
    print()
    
    # Criar arquivos
    print("📝 Criando arquivos de configuração...")
    for filepath, content in FILES.items():
        # Proteção extra: não sobrescrever arquivos sensíveis se já existirem
        if filepath in ["main.py", ".env"] and Path(filepath).exists():
            print(f"   ⏭️ Pulando {filepath} (Já existe e foi configurado manualmente)")
            continue
            
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"   ✅ {filepath}")
    
    print()
    print("=" * 60)
    print("✅ SETUP SEGURO CONCLUÍDO!")
    print("=" * 60)

if __name__ == "__main__":
    create_project_structure()