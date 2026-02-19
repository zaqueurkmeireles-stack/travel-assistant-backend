"""
TravelCompanion AI - Setup Master 100% Automático
Executa: python setup_project.py
Cria TODA a estrutura do MVP Completo automaticamente
"""

import os
from pathlib import Path

# ============================================================
# SUAS KEYS REAIS (JÁ PREENCHIDAS AUTOMATICAMENTE)
# ============================================================

API_KEYS = {
    "OPENAI_API_KEY": "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",
    "GOOGLE_GEMINI_API_KEY": "AIzaSyAzfAKYG01KHOKyFt8r9INbmgzfjcf0ayM",
    "GOOGLE_MAPS_API_KEY": "AIzaSyAl-uUlCM-JDd398Qsa_tyhX-dVoOwB75o",
    "OPENWEATHER_API_KEY": "6d2f79674c36b116946da1f15b85fc42",
    "TAVILY_API_KEY": "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",
    "AERODATABOX_API_KEY": "cb44b2d1acmsha7db96ec5484957p11b134jsn13348b425ba0",
    "FOURSQUARE_API_KEY": "fsqhDT4oMj2BxiTg7wM04qEJUDSV3P90blU5lzN7bVN9JM=",
    "ELEVENLABS_API_KEY": "sk_56d0072b7eaf744e3e912966a1a13b76afea02d59c074572",
    "N8N_API_KEY": "429683C4C977415CAAFCCE10F7D57E11",
}

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
# .ENV (AUTOMÁTICO COM SUAS KEYS)
# ============================================================
FILES[".env"] = f"""# ============================================================
# TRAVELCOMPANION AI - CONFIGURAÇÃO AUTOMÁTICA
# ============================================================

# INTELIGÊNCIA ARTIFICIAL
OPENAI_API_KEY={API_KEYS['OPENAI_API_KEY']}
GOOGLE_GEMINI_API_KEY={API_KEYS['GOOGLE_GEMINI_API_KEY']}
ENABLE_DUAL_AI_CONSENSUS=True

# WHATSAPP (Preencher quando configurar)
WHATSAPP_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_VERIFY_TOKEN=meu-token-verificacao-123

# GOOGLE MAPS
GOOGLE_MAPS_API_KEY={API_KEYS['GOOGLE_MAPS_API_KEY']}

# BUSCA
TAVILY_API_KEY={API_KEYS['TAVILY_API_KEY']}

# VOOS
AERODATABOX_API_KEY={API_KEYS['AERODATABOX_API_KEY']}
AERODATABOX_API_HOST=aerodatabox.p.rapidapi.com

# CLIMA
OPENWEATHER_API_KEY={API_KEYS['OPENWEATHER_API_KEY']}

# LOCAIS
FOURSQUARE_API_KEY={API_KEYS['FOURSQUARE_API_KEY']}

# SÍNTESE DE VOZ
ELEVENLABS_API_KEY={API_KEYS['ELEVENLABS_API_KEY']}

# N8N
N8N_API_KEY={API_KEYS['N8N_API_KEY']}
N8N_WEBHOOK_URL=

# REDDIT (Adicione quando precisar)
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=travel_assistant:v1.0

# ============================================================
# ADICIONE NOVAS APIs AQUI (EXEMPLO)
# ============================================================
# NOVA_API_KEY=sua_key_aqui
# OUTRA_API_KEY=outra_key_aqui

# SEGURANÇA
API_SECRET_KEY=travel-companion-secret-key-change-in-production

# CONFIGURAÇÕES
ENVIRONMENT=development
PORT=8000
DEBUG=True
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000

# BANCO DE DADOS
CHROMA_DB_PATH=./data/chroma_db
DOCUMENTS_PATH=./data/documents
"""

# ============================================================
# MAIN.PY
# ============================================================
FILES["main.py"] = '''"""
TravelCompanion AI - MVP Completo
Servidor FastAPI principal com estrutura modular
"""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings, setup_directories

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
'''

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
# GUIA DE EXPANSÃO (Corrigido para não quebrar a cópia)
# ============================================================
FILES["EXPANSAO.md"] = """# Guia de Expansão - Como Adicionar Novas APIs

## Processo Simples em 3 Passos:

### PASSO 1: Adicionar no .env
Abra o arquivo .env e adicione sua nova API:
`NOVA_API_KEY=sua_chave_aqui`

### PASSO 2: Adicionar no app/config.py
Adicione o campo na classe Settings:
`NOVA_API_KEY: Optional[str] = None`

### PASSO 3: Usar nos seus serviços
Importe as configurações e use a chave em qualquer lugar do projeto:

    from app.config import settings
    print(settings.NOVA_API_KEY)
"""

# ============================================================
# INJEÇÃO AUTOMÁTICA DE __INIT__.PY (Restauração)
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
    print("🚀 TRAVELCOMPANION AI - MVP COMPLETO")
    print("=" * 60)
    print()
    
    # Criar pastas
    print("📁 Criando estrutura de pastas...")
    for folder in FOLDERS:
        Path(folder).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {folder}")
    
    print()
    
    # Criar arquivos
    print("📝 Criando arquivos...")
    for filepath, content in FILES.items():
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"   ✅ {filepath}")
    
    print()
    print("=" * 60)
    print("✅ PROJETO CRIADO COM SUCESSO!")
    print("=" * 60)
    print()
    print("📋 PRÓXIMOS PASSOS:")
    print()
    print("1️⃣  Instalar dependências:")
    print("   pip install -r requirements.txt")
    print()
    print("2️⃣  Executar servidor FastAPI:")
    print("   python main.py")
    print()
    print("=" * 60)

if __name__ == "__main__":
    create_project_structure()