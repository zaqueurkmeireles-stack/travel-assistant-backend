import sys
# PATCH routes.py - adicionar endpoints faltantes
rpath = '/app/app/api/routes.py'
with open(rpath, 'r') as f:
    r = f.read()
if '/webhook/media' in r:
    print('PATCH 1: webhook/media ja existe')
else:
    # Adicionar imports se nao existem
    if 'DocumentIngestor' not in r:
        r = r.replace(
            'from app.agents.orchestrator import TravelAgent',
            'from app.agents.orchestrator import TravelAgent\nfrom app.services.document_ingestor import DocumentIngestor\nfrom app.services.n8n_service import N8nService'
        )
    if 'BackgroundTasks' not in r:
        r = r.replace(
            'from fastapi import APIRouter',
            'from fastapi import APIRouter, BackgroundTasks'
        )
    if 'MediaRequest' not in r:
        # Adicionar modelos antes de ChatResponse
        models = (
            'class MediaRequest(BaseModel):\n'
            '    user_id: str\n'
            '    base64: str\n'
            '    filename: str\n'
            '    mimetype: str\n\n'
            'class LocationRequest(BaseModel):\n'
            '    user_id: str\n'
            '    latitude: float\n'
            '    longitude: float\n'
            '    address: Optional[str] = None\n\n'
        )
        r = r.replace('class ChatResponse', models + 'class ChatResponse')
    # Garantir que BackgroundTasks esta no chat_endpoint
    if 'background_tasks: BackgroundTasks' not in r:
        r = r.replace(
            'async def chat_endpoint(request: ChatRequest',
            'async def chat_endpoint(request: ChatRequest, background_tasks: BackgroundTasks'
        )
    # Adicionar endpoints no final
    r += '\n'
    r += '@router.post("/webhook/media")\n'
    r += 'async def media_webhook(request: MediaRequest, background_tasks: BackgroundTasks):\n'
    r += '    logger.info(f"Recebendo midia ({request.filename}) de {request.user_id}")\n'
    r += '    try:\n'
    r += '        ingestor = DocumentIngestor()\n'
    r += '        data_payload = {\n'
    r += '            "key": {"remoteJid": f"{request.user_id}@s.whatsapp.net"},\n'
    r += '            "message": {"documentMessage": {"fileName": request.filename, "mimetype": request.mimetype}},\n'
    r += '            "base64": request.base64\n'
    r += '        }\n'
    r += '        result = ingestor.ingest_from_webhook(data_payload)\n'
    r += '        if result.get("success"):\n'
    r += '            doc_type = result.get("document_type", "documento")\n'
    r += '            def send_confirmation_and_gap_analysis():\n'
    r += '                try:\n'
    r += '                    n8n = N8nService()\n'
    r += '                    confirm_msg = "Documento recebido e salvo!"\n'
    r += '                    confirm_msg += "\\nArquivo: " + request.filename\n'
    r += '                    confirm_msg += "\\nTipo: " + doc_type + "\\n"\n'
    r += '                    from app.services.rag_service import RAGService\n'
    r += '                    rag = RAGService()\n'
    r += '                    user_docs = rag.list_user_documents(request.user_id)\n'
    r += '                    found = set()\n'
    r += '                    for d in user_docs:\n'
    r += '                        nl = d.lower() if d else ""\n'
    r += '                        if any(w in nl for w in ["passagem","ticket","boarding","flight","voo"]): found.add("passagem")\n'
    r += '                        if any(w in nl for w in ["hotel","reserva","booking"]): found.add("hotel")\n'
    r += '                        if any(w in nl for w in ["seguro","insurance","apolice"]): found.add("seguro")\n'
    r += '                    if doc_type: found.add(doc_type.lower())\n'
    r += '                    missing = []\n'
    r += '                    for k,v in {"passagem":"Passagens aereas","hotel":"Reserva de hotel","seguro":"Seguro viagem"}.items():\n'
    r += '                        if k not in found: missing.append(v)\n'
    r += '                    if missing:\n'
    r += '                        confirm_msg += "\\nDocumentos pendentes:"\n'
    r += '                        for m in missing: confirm_msg += "\\n- " + m\n'
    r += '                        confirm_msg += "\\nEnvie os documentos faltantes aqui no chat!"\n'
    r += '                    else:\n'
    r += '                        confirm_msg += "\\nTodos os documentos essenciais salvos!"\n'
    r += '                    n8n.enviar_resposta_usuario(request.user_id, confirm_msg)\n'
    r += '                except Exception as e:\n'
    r += '                    logger.error(f"Erro confirmacao: {e}")\n'
    r += '            background_tasks.add_task(send_confirmation_and_gap_analysis)\n'
    r += '            return {"success": True, "message": f"Documento {request.filename} indexado!"}\n'
    r += '        else:\n'
    r += '            return JSONResponse(status_code=422, content=result)\n'
    r += '    except Exception as e:\n'
    r += '        logger.error(f"Erro webhook midia: {e}")\n'
    r += '        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})\n'
    r += '\n'
    r += '@router.post("/webhook/location")\n'
    r += 'async def location_webhook(request: LocationRequest, agent: TravelAgent = Depends(get_agent)):\n'
    r += '    logger.info(f"Geolocalizacao: {request.user_id} em {request.latitude}, {request.longitude}")\n'
    r += '    try:\n'
    r += '        from app.services.maps_service import GoogleMapsService\n'
    r += '        maps = GoogleMapsService()\n'
    r += '        geo_info = maps.reverse_geocode(request.latitude, request.longitude)\n'
    r += '        from datetime import datetime\n'
    r += '        today_str = datetime.now().strftime("%Y-%m-%d")\n'
    r += '        prompt = f"SISTEMA: Usuario em {geo_info}. Coords: {request.latitude},{request.longitude}. Data: {today_str}. Analise RAG e gere guia proativo ou responda IGNORE."\n'
    r += '        response = agent.chat(user_input=prompt, thread_id=request.user_id)\n'
    r += '        if response and "IGNORE" not in response:\n'
    r += '            n8n = N8nService()\n'
    r += '            n8n.enviar_resposta_usuario(request.user_id, response)\n'
    r += '            return {"success": True, "proactive_sent": True}\n'
    r += '        return {"success": True, "proactive_sent": False}\n'
    r += '    except Exception as e:\n'
    r += '        logger.error(f"Erro geoguia: {e}")\n'
    r += '        return {"success": False, "error": str(e)}\n'
    with open(rpath, 'w') as f:
        f.write(r)
    print('PATCH 1 OK: endpoints media + location adicionados')

# PATCH 2: orchestrator.py
opath = '/app/app/agents/orchestrator.py'
with open(opath, 'r') as f:
    o = f.read()
if 'Recebimento de Documentos via WhatsApp' in o:
    print('PATCH 2: prompt ja atualizado')
else:
    s1 = o.find('system_prompt = """')
    s2 = o.find('"""', s1 + 20) + 3
    if s1 != -1:
        np = 'system_prompt = """Voce e o **Seven Assistant Travel**, o guia de viagem definitivo e concierge pessoal.\n'
        np += 'Sua missao e acompanhar o usuario por todo o percurso da viagem.\n\n'
        np += '### Suas diretrizes de ouro:\n\n'
        np += '1. **Recebimento de Documentos via WhatsApp:** O usuario PODE e DEVE enviar documentos de viagem diretamente neste chat. Passagens, hotel, seguro, carro - tudo em PDF, foto ou imagem. Confirme que SIM quando perguntarem.\n\n'
        np += '2. **Conhecimento Profundo (RAG):** Consulte os documentos do usuario antes de responder. Saiba datas, horarios e codigos de reserva de cor.\n\n'
        np += '3. **Gap Analysis Proativa:** Analise o que FALTA. Se enviou passagem mas nao seguro, pergunte carinhosamente.\n\n'
        np += '4. **Checkpoints Proativos:** D-7 (documentacao, vistos), D-1 (check-in, fuso horario), D-0 (guiche, portao), Chegada (mapas offline, rota).\n\n'
        np += '5. **Guia de Geolocalizacao:** Use localizacao para dar direcoes precisas.\n\n'
        np += '6. **Economia de Dados:** Ofereca opcoes de texto ou mapa offline.\n\n'
        np += '7. **Viagens Compartilhadas:** Pergunte se quer compartilhar docs com outro viajante.\n\n'
        np += '8. **Alertas de Conectividade:** Sugira mapas offline no dia anterior.\n\n'
        np += '9. **Estilo:** Seja prestativo e passe seguranca. Voce e o guardiao da viagem.\n\n'
        np += 'Leia vouchers para dar direcoes proativas sobre portao, guiche e check-in.\n"""'
        o = o[:s1] + np + o[s2:]
        with open(opath, 'w') as f:
            f.write(o)
        print('PATCH 2 OK: system prompt atualizado com 9 diretrizes')
    else:
        print('ERRO: system_prompt nao encontrado')

# Verificacao final
c = open(rpath).read()
print(f'routes.py: {len(c.splitlines())} linhas')
print(f'  /webhook/media: {"SIM" if "/webhook/media" in c else "NAO"}')
print(f'  /webhook/location: {"SIM" if "/webhook/location" in c else "NAO"}')
print(f'  gap_analysis: {"SIM" if "gap_analysis" in c else "NAO"}')
o2 = open(opath).read()
print(f'  prompt_v2: {"SIM" if "Recebimento de Documentos" in o2 else "NAO"}')
print('CONCLUIDO')
