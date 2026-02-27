"""
Document Ingestor - Orquestra o download, parse e indexação de documentos no RAG.
"""

import requests
from app.services.rag_service import RAGService
from app.services.trip_service import TripService
from app.parsers.parser_factory import ParserFactory
from loguru import logger
from typing import Dict, Any, Optional

class DocumentIngestor:
    """Orquestrador de ingestão de documentos"""
    
    def __init__(self):
        self.rag_svc = RAGService()
        self.trip_svc = TripService()
        self.parser_factory = ParserFactory()
        logger.info("✅ DocumentIngestor inicializado")
        
    def ingest_from_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa o payload do Evolution API e indexa no RAG"""
        try:
            # 1. Extrair informações básicas
            message = data.get("message", {})
            sender_number = data.get("key", {}).get("remoteJid", "").split("@")[0] or data.get("sender", "unknown")
            
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
            # No Evolution API, a mídia pode vir como base64 ou URL dependendo da config.
            # Se vier base64 no campo 'base64':
            base64_data = data.get("base64")
            
            if base64_data:
                import base64
                file_content = base64.b64decode(base64_data)
                logger.info(f"📥 Arquivo recebido via Base64: {filename}")
            else:
                # Se não vier base64, tentamos simular ou buscar via URL (se implementado no futuro)
                logger.warning("Conteúdo binário não encontrado no payload (base64 vazio).")
                return {"success": False, "error": "Conteúdo do arquivo não encontrado no webhook."}
            
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
            trip = self.trip_svc.add_trip_from_doc(sender_number, parse_result)
            
            from app.services.user_service import UserService
            user_service = UserService()
            
            if trip:
                logger.info(f"📅 Viagem vinculada: {trip['destination']} em {trip['start_date']}")
                user_service.set_active_trip(sender_number, trip["id"])
                
            active_trip = user_service.get_active_trip(sender_number)
            
            # 5. Remover documentos antigos do mesmo tipo antes de indexar
            doc_type = parse_result.get("document_type", "geral")
            removed = self.rag_svc.delete_documents_by_type(sender_number, doc_type, active_trip)
            if removed:
                logger.info(f"🔄 {removed} versão(ões) anterior(es) do tipo '{doc_type}' substituída(s)")
            
            # 6. Indexar no RAG com o Trip ID
            metadata = {
                "filename": filename,
                "thread_id": sender_number,
                "trip_id": active_trip,
                "mimetype": mimetype,
                "document_type": doc_type
            }
            
            self.rag_svc.add_document(extracted_text, metadata)
            
            # 7. Detectar se outro usuário tem viagem similar (mesma dest + data ±3 dias)
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
            
            logger.info(f"✨ Ingestão concluída com sucesso: {filename}")
            return {
                "success": True, 
                "filename": filename, 
                "document_type": metadata["document_type"],
                "text_preview": extracted_text[:100],
                "trip_match": trip_match  # None se não houver viagem similar
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na ingestão do documento: {e}")
            return {"success": False, "error": str(e)}

