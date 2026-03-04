"""
Document Ingestor - Orquestra o download, parse e indexação de documentos no RAG.
"""

import requests
from app.services.rag_service import RAGService
from app.services.trip_service import TripService
from app.services.google_drive_service import GoogleDriveService
from app.parsers.parser_factory import ParserFactory
from loguru import logger
from typing import Dict, Any, Optional

class DocumentIngestor:
    """Orquestrador de ingestão de documentos"""
    
    def __init__(self):
        self.rag_svc = RAGService()
        self.trip_svc = TripService()
        self.drive_svc = GoogleDriveService()
        self.parser_factory = ParserFactory()
        logger.info("✅ DocumentIngestor inicializado")
        
    def ingest_from_webhook(self, data: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """Processa o payload do Evolution API e indexa no RAG. Se dry_run=True, apenas parseia e busca matches."""
        try:
            # 1. Extrair informações básicas
            message = data.get("message", {})
            raw_sender = data.get("key", {}).get("remoteJid", "").split("@")[0] or data.get("sender", "unknown")
            from app.services.user_service import UserService
            user_svc = UserService()
            sender_number = user_svc.normalize_phone(raw_sender)
            logger.info(f"📥 Ingestão para: {sender_number} (Original: {raw_sender})")
            
            # Identificar se é documento ou imagem
            doc_msg = message.get("documentMessage")
            img_msg = message.get("imageMessage")
            
            target = doc_msg or img_msg
            if not target:
                logger.warning("Payload não contém documento ou imagem reconhecível.")
                return {"success": False, "error": "Tipo de mídia não suportado."}
            
            filename = target.get("fileName", "arquivo_recebido")
            mimetype = target.get("mimetype", "")
            
            # Garantir que o arquivo tenha extensão baseada no mimetype (WhatsApp às vezes omite)
            if mimetype == "application/pdf" and not filename.lower().endswith(".pdf"):
                filename += ".pdf"
                logger.info(f"📎 Extensão .pdf adicionada automaticamente: {filename}")
            elif mimetype in ["image/jpeg", "image/jpg"] and not filename.lower().endswith((".jpg", ".jpeg")):
                filename += ".jpg"
            elif mimetype == "image/png" and not filename.lower().endswith(".png"):
                filename += ".png"
            
            # 2. Obter o conteúdo do arquivo
            base64_data = data.get("base64")
            message_id = data.get("message_id") or data.get("key", {}).get("id")
            
            if base64_data:
                import base64
                file_content = base64.b64decode(base64_data)
                logger.info(f"📥 Arquivo recebido via Base64: {filename}")
            elif message_id:
                # 🚀 FALLBACK: Se não veio Base64 (comum em encaminhamentos), buscar via API REST
                from app.services.evolution_service import EvolutionService
                evo_svc = EvolutionService()
                remote_jid = data.get("user_id")
                file_content = evo_svc.get_message_content(message_id, remote_jid)
                
                if file_content:
                    logger.info(f"✅ Arquivo recuperado via API REST (MessageID: {message_id})")
                else:
                    logger.warning(f"⚠️ Falha ao recuperar arquivo via API REST para {message_id}")
                    return {
                        "success": False, 
                        "error": "Não consegui ler o conteúdo deste arquivo encaminhado. Por favor, tente enviar o arquivo diretamente (sem encaminhar) ou mande um novo print."
                    }
            else:
                logger.warning("Conteúdo binário não encontrado no payload e message_id ausente.")
                return {"success": False, "error": "Conteúdo do arquivo não encontrado no webhook."}

            # [NOVO] Se for imagem ou vídeo (não documento PDF/Docx), salvar no Google Drive
            is_media = mimetype.startswith("image") or mimetype.startswith("video")
            is_doc = mimetype in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
            
            drive_link = None
            if is_media and not is_doc:
                # Buscar trip ativa para saber o nome da pasta
                from app.services.user_service import UserService
                user_svc = UserService()
                active_trip_id = user_svc.get_active_trip(sender_number)
                
                # Se não houver viagem ativa, usamos uma pasta genérica para o usuário
                # Se houver, usamos a pasta unificada da viagem
                trip_folder_key = active_trip_id or f"User_{sender_number}"
                trip_name = "Mídia Diversas"
                
                if active_trip_id:
                    for t in self.trip_svc.trips:
                        if t["id"] == active_trip_id:
                            trip_name = t["destination"]
                            break
                
                folder_id = self.drive_svc.get_trip_media_folder(trip_folder_key, trip_name)
                if folder_id and not dry_run:
                    file_id = self.drive_svc.upload_file(file_content, filename, mimetype, folder_id)
                    drive_link = f"https://drive.google.com/file/d/{file_id}/view"
                    logger.info(f"📸 Mídia salva no Drive: {drive_link}")
                
                # Se for APENAS foto de viagem (sem texto de documento), podemos parar aqui ou 
                # continuar se o usuário quiser análise de imagem via Gemini/Vision
                if not any(ext in filename.lower() for ext in [".pdf", ".docx"]):
                    return {
                        "success": True, 
                        "filename": filename, 
                        "document_type": "media",
                        "drive_link": drive_link,
                        "message": "Foto/Vídeo salvo com sucesso na sua pasta da viagem no Google Drive!"
                    }
            
            # 3. Parsear o texto
            parse_result = self.parser_factory.auto_parse(file_content, filename)
            
            if not parse_result.get("success", True): # Fallback True se não houver campo success
                return {"success": False, "error": parse_result.get("error", "Falha no parse")}
            
            extracted_text = parse_result.get("raw_text", "")
            # Se o parser retornou um dicionário estruturado mas não o texto bruto, 
            # podemos concatenar os campos importantes
            if not extracted_text:
                extracted_text = str(parse_result)
            
            # 4. Registrar ou atualizar a Viagem com base no documento
            trip = None
            if not dry_run:
                trip = self.trip_svc.add_trip_from_doc(sender_number, parse_result)
            else:
                # Em dry_run, apenas extraímos a trip para match, sem salvar
                trip = self.trip_svc.extract_trip_data(parse_result)
            
            from app.services.user_service import UserService
            user_service = UserService()
            
            if trip and not dry_run:
                logger.info(f"📅 Viagem vinculada: {trip['destination']} en {trip['start_date']}")
                user_service.set_active_trip(sender_number, trip["id"])
                
            active_trip = user_service.get_active_trip(sender_number)
            
            # 5. [SMART DEDUPLICATOR] Detectar conflitos de passageiro/tipo/segmento
            doc_type = parse_result.get("document_type", "geral")
            traveler = parse_result.get("primary_traveler_name")
            segment = parse_result.get("segment_info")
            is_travel = parse_result.get("is_travel_content", True)
            
            if not is_travel and not dry_run:
                logger.warning(f"⚠️ Documento considerado irrelevante: {filename}. Suspendendo indexação.")
                return {
                    "success": True,
                    "status": "irrelevant",
                    "filename": filename,
                    "document_type": doc_type,
                    "traveler": traveler,
                    "mimetype": mimetype,
                    "text": extracted_text,
                    "metadata": {
                        "filename": filename,
                        "thread_id": sender_number,
                        "trip_id": active_trip,
                        "mimetype": mimetype,
                        "document_type": doc_type,
                        "primary_traveler_name": traveler,
                        "segment_info": segment
                    },
                    "is_travel_content": False
                }
            
            if not dry_run:
                # Buscar se já existe documento deste tipo no RAG
                has_conflict = False
                for doc in self.rag_svc.documents:
                    m = doc["metadata"]
                    # Mesmo usuário (ou trip) e mesmo tipo
                    same_scope = (m.get("thread_id") == sender_number or m.get("trip_id") == active_trip)
                    same_type = m.get("document_type") == doc_type
                    
                    if same_scope and same_type:
                        # Se for documento pessoal (passagem, seguro), avalia o passageiro e segmento
                        if doc_type.lower() in ["passagem", "seguro"]:
                            if traveler and m.get("primary_traveler_name") == traveler:
                                if segment and m.get("segment_info"):
                                    if segment.lower() == m.get("segment_info", "").lower():
                                        has_conflict = True
                                        break
                                else:
                                    has_conflict = True
                                    break
                        else:
                            # Para roteiro, locação de carro, hotel, apenas o mesmo tipo no mesmo escopo gera conflito
                            # pois geralmente só há um roteiro ou reserva de locação (ou queremos avisar o usuário da reescrita)
                            has_conflict = True
                            break
                
                if has_conflict:
                    logger.info(f"⚠️ Conflito detectado: {doc_type} para {traveler} ({segment or 'geral'}) já existe.")
                    return {
                        "success": True,
                        "status": "conflict",
                        "document_type": doc_type,
                        "traveler": traveler,
                        "segment": segment,
                        "filename": filename,
                        "extracted_data": parse_result,
                        "mimetype": mimetype,
                        "text": extracted_text,
                        "is_travel_content": parse_result.get("is_travel_content", True)
                    }
            
            # 6. Remover versão anterior do MESMO ARQUIVO se existir (Update simples por nome)
            if not dry_run:
                removed = self.rag_svc.delete_documents_by_type(sender_number, doc_type, active_trip, filename)
                if removed:
                    logger.info(f"🔄 Arquivo '{filename}' anterior substituído por nova versão.")
            
            # 7. Indexar no RAG com o Trip ID e Metadados estendidos
            metadata = {
                "filename": filename,
                "thread_id": sender_number,
                "trip_id": active_trip,
                "mimetype": mimetype,
                "document_type": doc_type,
                "primary_traveler_name": traveler,
                "segment_info": parse_result.get("segment_info")
            }
            
            if not dry_run:
                # ✂️ Lógica de Chunking: divide textos grandes em pedaços menores
                chunk_size = 4000
                overlap = 200
                chunks = []
                
                if len(extracted_text) > chunk_size:
                    for i in range(0, len(extracted_text), chunk_size - overlap):
                        chunk = extracted_text[i:i + chunk_size]
                        chunks.append(chunk)
                    logger.info(f"✂️ Documento fatiado em {len(chunks)} chunks para indexação.")
                else:
                    chunks = [extracted_text]

                for chunk_content in chunks:
                    self.rag_svc.add_document(chunk_content, metadata)
            
            # 8. Detectar se outro usuário tem viagem similar (mesma dest + data ±3 dias)
            trip_match = None
            if trip:
                similar = self.trip_svc.find_similar_trips(
                    exclude_user_id=sender_number,
                    destination=trip.get("destination", ""),
                    start_date=trip.get("start_date", "")
                )
                if similar:
                    logger.info(f"🔗 Viagem similar detectada! Host: {similar['host_user_id']}")
                    trip_match = {
                        "host_user_id": similar["host_user_id"],
                        "trip_id": similar["trip"]["id"],
                        "destination": similar["trip"]["destination"],
                        "start_date": similar["trip"]["start_date"]
                    }

            # 8. Auditoria Inteligente (Gap Analysis) - Proativo
            audit_report = None
            if trip and trip.get("start_date") and trip.get("end_date"):
                from app.services.trip_audit_service import TripAuditService
                audit_svc = TripAuditService()
                audit_data = audit_svc.audit_trip(sender_number, trip["id"], trip)
                if audit_data.get("nights_covered", 0) < audit_data.get("trip_duration_days", 0) or audit_data.get("other_missing_items"):
                    audit_report = audit_svc.generate_human_report(audit_data)
            
            logger.info(f"✨ Ingestão concluída com sucesso: {filename}")
            return {
                "success": True, 
                "filename": filename, 
                "document_type": metadata["document_type"],
                "text_preview": extracted_text[:100],
                "is_travel_content": parse_result.get("is_travel_content", True),
                "trip_match": trip_match,
                "audit_report": audit_report  # Contém alerta proativo se houver gaps
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na ingestão do documento: {e}")
            return {"success": False, "error": str(e)}

