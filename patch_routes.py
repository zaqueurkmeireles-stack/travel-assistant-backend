import re

file_path = "app/api/routes.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Adicionando o import do Orquestrador no topo do arquivo (se não existir)
if "from app.services.ai_orchestrator import AIOrchestrator" not in content:
    # Insere logo após os imports do fastapi
    content = re.sub(
        r'(from fastapi import.*?\n)',
        r'\1from app.services.ai_orchestrator import AIOrchestrator\n',
        content,
        count=1
    )

# 2. Localizando a rota /chat e substituindo a lógica interna
# Padrão: acha o @router.post("/chat"... e tudo até o return
pattern = r'(@router\.post\("/chat".*?def chat_endpoint.*?:\n)(.*?)(?=\n@router|\Z)'

# Nova lógica que chama o orquestrador
new_logic = """
    try:
        from app.services.idempotency_service import IdempotencyService
        idempotency = IdempotencyService()
        
        if idempotency.is_processed(request.message_id):
            return ChatResponse(status="RESPONDED", message="Mensagem já processada anteriormente.")
            
        # Instancia o Orquestrador da Tríade
        orchestrator = AIOrchestrator()
        
        # Chama a inteligência de Consenso
        # Estamos passando a mensagem do usuário (request.message)
        final_response = await orchestrator.process_message(request.message)
        
        # Marca como processado
        idempotency.mark_processed(request.message_id, "RESPONDED")
        
        return ChatResponse(status="SUCCESS", message=final_response)
        
    except Exception as e:
        from loguru import logger
        logger.error(f"Erro Crítico no Endpoint de Chat: {e}")
        return ChatResponse(status="ERROR", message="Desculpe, nosso sistema encontrou uma falha ao consultar os agentes de viagem.")
"""

# Substituição segura
if re.search(pattern, content, flags=re.DOTALL):
    content = re.sub(pattern, r'\1' + new_logic, content, flags=re.DOTALL)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ Cérebro transplantado com sucesso! Rota /chat agora usa a Tríade de IAs.")
else:
    print("⚠️ Não foi possível achar a rota /chat com a assinatura padrão. Verifique o routes.py.")
