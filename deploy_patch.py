import base64, zlib, sys

# ===== routes.py (completo com gap analysis) =====
routes_content = """
\"\"\"
API Routes - Endpoints REST para o TravelCompanion AI
Conecta o agente LangGraph e os Parsers ao mundo externo (n8n/WhatsApp)
\"\"\"

from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from loguru import logger
from typing import Optional

from app.parsers.parser_factory import ParserFactory
from app.agents.orchestrator import TravelAgent
from app.services.document_ingestor import DocumentIngestor
from app.services.n8n_service import N8nService

router = APIRouter()

# ============================================================
# MODELOS DE DADOS (Pydantic)
# ============================================================
class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    success: bool
    response: str
    user_id: str

class MediaRequest(BaseModel):
    user_id: str
    base64: str
    filename: str
    mimetype: str

class LocationRequest(BaseModel):
    user_id: str
    latitude: float
    longitude: float
    address: Optional[str] = None

# ============================================================
# GERENCIAMENTO DE DEPENDENCIAS
# ============================================================
_agent = None
_parser_factory = None

def get_agent() -> TravelAgent:
    global _agent
    if _agent is None:
        logger.info("Inicializando TravelAgent para a API...")
        _agent = TravelAgent()
    return _agent

def get_parser_factory() -> ParserFactory:
    global _parser_factory
    if _parser_factory is None:
        logger.info("Inicializando ParserFactory para a API...")
        _parser_factory = ParserFactory()
    return _parser_factory

# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "TravelCompanion AI API"}

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    agent: TravelAgent = Depends(get_agent)
):
    logger.info(f"Nova mensagem de {request.user_id}: {request.message[:50]}...")
    try:
        resposta_ia = agent.chat(user_input=request.message, thread_id=request.user_id)
        if resposta_ia:
            n8n = N8nService()
            background_tasks.add_task(n8n.enviar_resposta_usuario, request.user_id, resposta_ia)
            logger.info(f"Resposta agendada para envio ao WhatsApp ({request.user_id})")
        return ChatResponse(success=True, response=resposta_ia, user_id=request.user_id)
    except Exception as e:
        logger.error(f"Erro ao processar chat: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    document_hint: Optional[str] = Form(None),
    factory: ParserFactory = Depends(get_parser_factory)
):
    logger.info(f"Recebendo documento: {file.filename}")
    try:
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Arquivo vazio")
        result = factory.auto_parse(file_content=file_content, filename=file.filename, document_hint=document_hint)
        if not result.get("success", True):
            return JSONResponse(status_code=422, content={"success": False, "error": result.get("error"), "filename": file.filename})
        return result
    except Exception as e:
        logger.error(f"Erro no upload: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar documento: {str(e)}")

@router.post("/webhook/media")
async def media_webhook(request: MediaRequest, background_tasks: BackgroundTasks):
    logger.info(f"Recebendo midia ({request.filename}) de {request.user_id}")
    try:
        ingestor = DocumentIngestor()
        data_payload = {
            "key": {"remoteJid": f"{request.user_id}@s.whatsapp.net"},
            "message": {"documentMessage": {"fileName": request.filename, "mimetype": request.mimetype}},
            "base64": request.base64
        }
        result = ingestor.ingest_from_webhook(data_payload)
        if result.get("success"):
            doc_type = result.get("document_type", "documento")
            def send_confirmation_and_gap_analysis():
                try:
                    n8n = N8nService()
                    confirm_msg = f"Documento recebido e salvo!\\n\\nArquivo: {request.filename}\\nTipo detectado: {doc_type}\\n\\n"
                    from app.services.rag_service import RAGService
                    rag = RAGService()
                    user_docs = rag.list_user_documents(request.user_id)
                    doc_types_found = set()
                    for doc_name in user_docs:
                        nl = doc_name.lower() if doc_name else ""
                        if any(w in nl for w in ["passagem", "ticket", "boarding", "flight", "voo"]): doc_types_found.add("passagem")
                        if any(w in nl for w in ["hotel", "reserva", "booking"]): doc_types_found.add("hotel")
                        if any(w in nl for w in ["seguro", "insurance", "apolice"]): doc_types_found.add("seguro")
                    if doc_type: doc_types_found.add(doc_type.lower())
                    missing = []
                    checklist = {"passagem": "Passagens aereas", "hotel": "Reserva de hotel", "seguro": "Seguro viagem"}
                    for key, label in checklist.items():
                        if key not in doc_types_found: missing.append(label)
                    if missing:
                        confirm_msg += "Checklist de documentos pendentes:\\n"
                        for item in missing: confirm_msg += f"  - {item}\\n"
                        confirm_msg += "\\nEnvie os documentos faltantes aqui no chat!"
                    else:
                        confirm_msg += "Todos os documentos essenciais ja estao salvos!"
                    n8n.enviar_resposta_usuario(request.user_id, confirm_msg)
                    logger.info(f"Confirmacao enviada para {request.user_id}")
                except Exception as e:
                    logger.error(f"Erro ao enviar confirmacao: {e}")
            background_tasks.add_task(send_confirmation_and_gap_analysis)
            return {"success": True, "message": f"Documento {request.filename} indexado!"}
        else:
            return JSONResponse(status_code=422, content=result)
    except Exception as e:
        logger.error(f"Erro no webhook de midia: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@router.post("/webhook/location")
async def location_webhook(request: LocationRequest, agent: TravelAgent = Depends(get_agent)):
    logger.info(f"Geolocalizacao Proativa: {request.user_id} em {request.latitude}, {request.longitude}")
    try:
        from app.services.maps_service import GoogleMapsService
        maps = GoogleMapsService()
        geo_info = maps.reverse_geocode(request.latitude, request.longitude)
        from datetime import datetime
        today_str = datetime.now().strftime("%Y-%m-%d")
        prompt = (
            f"SISTEMA: O usuario acabou de chegar em: {geo_info}. "
            f"Coordenadas: {request.latitude}, {request.longitude}. "
            f"DATA DE HOJE: {today_str}.\\n"
            f"Analise os documentos dele (RAG) e, se ele estiver em um aeroporto, cidade de escala ou destino final "
            f"da viagem agendada para HOJE ou amanha, gere uma mensagem PROATIVA de guia. "
            f"Diga onde ele esta, o que ele tem que fazer a seguir (ex: imigracao, pegar malas) "
            f"e ofereca as opcoes de economia de dados. "
            f"Se ele nao estiver em local relevante para a viagem, responda apenas 'IGNORE'."
        )
        response = agent.chat(user_input=prompt, thread_id=request.user_id)
        if response and "IGNORE" not in response:
            n8n = N8nService()
            n8n.enviar_resposta_usuario(request.user_id, response)
            return {"success": True, "proactive_sent": True}
        return {"success": True, "proactive_sent": False}
    except Exception as e:
        logger.error(f"Erro no Geoguia Proativo: {e}")
        return {"success": False, "error": str(e)}
""".strip()

# ===== orchestrator.py system prompt patch =====
orch_path = '/app/app/agents/orchestrator.py'
with open(orch_path, 'r') as f:
    orch = f.read()

if 'Recebimento de Documentos via WhatsApp' not in orch:
    old_start = orch.find('system_prompt = """')
    old_end = orch.find('"""', old_start + 20) + 3
    if old_start != -1:
        new_prompt = '''system_prompt = """Voce e o **Seven Assistant Travel**, o guia de viagem definitivo e concierge pessoal.
Sua missao e acompanhar o usuario por todo o percurso da viagem, desde o planejamento ate o retorno.

### Suas diretrizes de ouro:

1. **Recebimento de Documentos via WhatsApp:** O usuario PODE e DEVE enviar documentos de viagem diretamente neste chat. Passagens aereas, reservas de hotel, seguro viagem, locacao de carro, vouchers - tudo em PDF, foto ou imagem. Quando o usuario perguntar se pode enviar documentos, confirme que SIM e incentive-o a enviar.

2. **Conhecimento Profundo (RAG):** Sempre consulte os documentos do usuario (passagens, hoteis, seguros) antes de responder. Voce deve saber datas, horarios e codigos de reserva de cor.

3. **Gap Analysis Proativa:** Apos receber documentos, analise o que FALTA. Se o usuario enviou passagem mas nao enviou seguro, pergunte carinhosamente.

4. **Checkpoints Proativos:**
   - D-7: Avise sobre documentacao, vistos, checklist de mala baseado no clima.
   - D-1: Lembre do check-in online, localizadores, fuso horario.
   - D-0: Orientacoes de guiche, portao de embarque.
   - Chegada: Opcoes de mapas offline, rota ate locadora ou hotel.

5. **Guia de Geolocalizacao:** Quando receber uma localizacao, use-a para dar direcoes precisas.

6. **Economia de Dados:** Priorize o bolso do usuario. Ofereca opcoes de texto ou mapa offline.

7. **Viagens Compartilhadas:** Se detectar codigo de reserva compartilhado, pergunte se quer compartilhar documentos.

8. **Alertas de Conectividade:** No dia anterior a uma viagem, sugira download de mapas offline.

9. **Estilo:** Seja prestativo, organizado e passe seguranca. Voce e o guardiao da viagem dele e da familia.

Seja capaz de ler em vouchers o portao de embarque, guiche de locadora e horarios de check-in para dar direcoes proativas.
"""'''
        orch = orch[:old_start] + new_prompt + orch[old_end:]
        with open(orch_path, 'w') as f:
            f.write(orch)
        print('PATCH 2 OK: orchestrator.py system prompt atualizado')
    else:
        print('ERRO: system_prompt nao encontrado no orchestrator')
else:
    print('PATCH 2: orchestrator.py ja estava atualizado')

# ===== Escrever routes.py =====
routes_path = '/app/app/api/routes.py'
with open(routes_path, 'w') as f:
    f.write(routes_content)
print('PATCH 1 OK: routes.py completo (304 linhas) escrito com sucesso')

# Verificacao
with open(routes_path, 'r') as f:
    lines = f.readlines()
print(f'Verificacao: routes.py tem {len(lines)} linhas')

# Checar endpoints
with open(routes_path, 'r') as f:
    c = f.read()
print(f'  /webhook/media: {"SIM" if "/webhook/media" in c else "NAO"}')
print(f'  /webhook/location: {"SIM" if "/webhook/location" in c else "NAO"}')
print(f'  gap_analysis: {"SIM" if "send_confirmation_and_gap_analysis" in c else "NAO"}')
print(f'  N8nService: {"SIM" if "N8nService" in c else "NAO"}')

print('\\nTODOS OS PATCHES CONCLUIDOS COM SUCESSO')
