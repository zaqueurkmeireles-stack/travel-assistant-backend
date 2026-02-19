"""
TravelCompanion AI - Criação Automática de Rotas da API
Executa: python create_routes.py
"""

import os
from pathlib import Path

FILES = {}

# ============================================================
# ROTAS DA API
# ============================================================
FILES["app/api/routes.py"] = '''"""
API Routes - Endpoints REST para o TravelCompanion AI
Conecta o agente LangGraph e os Parsers ao mundo externo (n8n/WhatsApp)
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from loguru import logger
from typing import Optional

# Imports dos nossos motores
from app.parsers.parser_factory import ParserFactory
from app.agents.orchestrator import TravelAgent

router = APIRouter()

# ============================================================
# MODELOS DE DADOS (Pydantic)
# ============================================================
class ChatRequest(BaseModel):
    user_id: str  # Número do WhatsApp (usado como thread_id na memória)
    message: str  # Mensagem do usuário

class ChatResponse(BaseModel):
    success: bool
    response: str
    user_id: str

# ============================================================
# GERENCIAMENTO DE DEPENDÊNCIAS (Singletons para Performance)
# ============================================================
_agent = None
_parser_factory = None

def get_agent() -> TravelAgent:
    """Retorna a instância global do TravelAgent (evita recompilar o grafo a cada request)"""
    global _agent
    if _agent is None:
        logger.info("⚙️ Inicializando TravelAgent para a API...")
        _agent = TravelAgent()
    return _agent

def get_parser_factory() -> ParserFactory:
    """Retorna a instância global da ParserFactory"""
    global _parser_factory
    if _parser_factory is None:
        logger.info("⚙️ Inicializando ParserFactory para a API...")
        _parser_factory = ParserFactory()
    return _parser_factory

# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/health")
async def health_check():
    """Health check - Verifica se a API está funcionando"""
    return {
        "status": "healthy",
        "service": "TravelCompanion AI API"
    }

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, agent: TravelAgent = Depends(get_agent)):
    """
    Endpoint principal de Chat (Webhook para n8n/WhatsApp)
    Recebe a mensagem, processa no LangGraph e retorna a resposta.
    """
    logger.info(f"📥 Nova mensagem de {request.user_id}: {request.message[:50]}...")
    
    try:
        # Passamos o user_id como thread_id para o LangGraph manter a memória da conversa
        resposta_ia = agent.chat(user_input=request.message, thread_id=request.user_id)
        
        return ChatResponse(
            success=True,
            response=resposta_ia,
            user_id=request.user_id
        )
    except Exception as e:
        logger.error(f"❌ Erro ao processar chat: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno no processamento do agente: {str(e)}"
        )

@router.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    document_hint: Optional[str] = Form(None),
    factory: ParserFactory = Depends(get_parser_factory)
):
    """
    Upload e parse de documento de viagem
    """
    logger.info(f"📤 Recebendo documento: {file.filename}")
    
    try:
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(status_code=400, detail="Arquivo vazio")
        
        # Parse automático usando a factory
        result = factory.auto_parse(
            file_content=file_content,
            filename=file.filename,
            document_hint=document_hint
        )
        
        if not result.get("success", True):  # Se tiver success=False, falhou
            logger.warning(f"⚠️ Parse falhou: {result.get('error')}")
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "error": result.get("error", "Erro desconhecido"),
                    "document_type": result.get("document_type"),
                    "filename": file.filename
                }
            )
        
        logger.info(f"✅ Parse concluído: {result.get('document_type')}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Erro no upload: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar documento: {str(e)}"
        )
'''

def update_main_py():
    """Lê o main.py atual e injeta o router sem quebrar as configurações originais"""
    main_path = Path("main.py")
    
    if not main_path.exists():
        print("⚠️ main.py não encontrado! Execute setup_project.py primeiro.")
        return False
        
    with open(main_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Verificar se já foi injetado
    if "from app.api.routes import router as api_router" in content:
        print("   ✅ As rotas já estão registradas no main.py!")
        return True
        
    # Injetar o import no topo (depois do último import)
    import_statement = "from app.api.routes import router as api_router\n"
    
    # Injetar o include_router logo após a criação do app
    router_statement = "\n# API Routes (Injetado automaticamente)\napp.include_router(api_router, prefix=\"/api\", tags=[\"API\"])\n"
    
    # Lógica simples de injeção
    lines = content.split('\n')
    new_lines = []
    app_created = False
    
    for line in lines:
        new_lines.append(line)
        
        # Acha onde terminam os imports principais (ex: from app.config...)
        if line.startswith("from app.config"):
            new_lines.append(import_statement.strip())
            
        # Acha onde o app é instanciado
        if line.startswith("app = FastAPI(") or (app_created and line.startswith(")")):
            if line.startswith("app = FastAPI("):
                if ")" in line:
                    new_lines.append(router_statement.strip())
                else:
                    app_created = True
            elif app_created and line.startswith(")"):
                app_created = False
                new_lines.append(router_statement.strip())

    # Gravar o novo main.py
    with open(main_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))
        
    print("   ✅ main.py atualizado com sucesso (Rotas injetadas de forma segura)!")
    return True

def create_routes():
    """Cria os arquivos de rotas e atualiza o main.py"""
    print("=" * 70)
    print("🌐 CRIANDO ROTAS DA API E CONECTANDO O AGENTE")
    print("=" * 70)
    print()
    
    # Criar arquivo routes.py
    for filepath, content in FILES.items():
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"   ✅ {filepath} criado!")
    
    print()
    print("🔄 Atualizando main.py...")
    update_main_py()
    
    print()
    print("=" * 70)
    print("✅ API E ROTAS CONFIGURADAS COM SUCESSO!")
    print("=" * 70)
    print()
    print("📋 Endpoints disponíveis no seu servidor:")
    print("   💬 POST /api/chat - Webhook para conectar o n8n/WhatsApp")
    print("   📄 POST /api/upload-document - Endpoint para parsing de PDFs")
    print("   💚 GET  /api/health - Verificação de status")
    print()
    print("🎯 PRÓXIMO PASSO:")
    print("   Execute o servidor principal com: python main.py")
    print("   E acesse a documentação em: http://localhost:8000/docs")

if __name__ == "__main__":
    create_routes()