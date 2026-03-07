"""
Document Ingestor - Orquestra o download, parse e indexação de documentos no RAG.
"""

import requests
from app.services.rag_service import RAGService
from app.services.trip_service import TripService
from app.services.google_drive_service import GoogleDriveService
from app.parsers.parser_factory import ParserFactory
from loguru import logger
from typing import Dict, Any, Optional, List
from app.config import settings

class DocumentIngestor:
    """Orquestrador de ingestão de documentos"""
    
    def __init__(self):
        self.rag_svc = RAGService()
        self.trip_svc = TripService()
        self.drive_svc = GoogleDriveService()
        self.parser_factory = ParserFactory()
        logger.info("✅ DocumentIngestor inicializado")
        
    def ingest_from_webhook(self, data: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """
        Orquestrador de Ingestão.
        Fase 1: Extração e ACK (Rápido)
        Fase 2: Processamento e Indexação (Pesado)
        """
        try:
            # 1. Extração básica
            message = data.get("message", {})
            raw_sender = data.get("key", {}).get("remoteJid", "").split("@")[0] or data.get("sender", "unknown")
            from app.services.user_service import UserService
            user_svc = UserService()
            sender_number = user_svc.normalize_phone(raw_sender)
            
            doc_msg = message.get("documentMessage")
            img_msg = message.get("imageMessage")
            target = doc_msg or img_msg
            
            if not target:
                return {"success": False, "error": "Mídia não reconhecida."}
            
            filename = target.get("fileName", "arquivo")
            mimetype = target.get("mimetype", "")
            
            # 2. Obter conteúdo
            base64_data = data.get("base64")
            message_id = data.get("message_id") or data.get("key", {}).get("id")
            file_content = None
            
            if base64_data:
                import base64
                file_content = base64.b64decode(base64_data)
            elif message_id:
                from app.services.evolution_service import EvolutionService
                evo_svc = EvolutionService()
                file_content = evo_svc.get_message_content(message_id, raw_sender)
                
            if not file_content:
                return {"success": False, "error": "Não foi possível recuperar o conteúdo do arquivo."}

            # 3. Processamento Pesado
            return self.process_document(
                file_content=file_content,
                filename=filename,
                mimetype=mimetype,
                sender_number=sender_number,
                dry_run=dry_run
            )
            
        except Exception as e:
            logger.error(f"❌ Erro na ingestão: {e}")
            return {"success": False, "error": str(e)}

    def process_document(self, file_content: bytes, filename: str, mimetype: str, sender_number: str, dry_run: bool = False) -> Dict[str, Any]:
        """Processamento pesado e indexação."""
        try:
            # A. Google Drive Upload (Imagens/Vídeos)
            is_media = mimetype.startswith("image") or mimetype.startswith("video")
            is_doc = mimetype in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
            drive_link = None
            
            from app.services.user_service import UserService
            user_svc = UserService()
            active_trip_id = user_svc.get_active_trip(sender_number)
            
            if (is_media or is_doc) and not dry_run:
                trip_folder_key = active_trip_id or f"User_{sender_number}"
                trip_name = "Documentos e Midia"
                if active_trip_id:
                    for t in self.trip_svc.trips:
                        if t["id"] == active_trip_id:
                            trip_name = t["destination"]
                            break
                folder_id = self.drive_svc.get_trip_media_folder(trip_folder_key, trip_name)
                if folder_id:
                    file_id = self.drive_svc.upload_file(file_content, filename, mimetype, folder_id)
                    drive_link = f"https://drive.google.com/file/d/{file_id}/view"
                    logger.info(f"📄 Arquivo salvo no Drive: {drive_link}")

            # Se for apenas mídia sem texto (print de conversa etc), e não for PDF
            if is_media and not is_doc and not any(ext in filename.lower() for ext in [".pdf", ".docx"]):
                return {
                    "success": True,
                    "filename": filename,
                    "document_type": "media",
                    "drive_link": drive_link,
                    "status": "success",
                    "message": "Imagens e vídeos são salvos diretamente no seu Google Drive."
                }

            # B. Parse
            parse_result = self.parser_factory.auto_parse(file_content, filename)
            if not parse_result.get("success", True):
                return {"success": False, "error": parse_result.get("error", "Erro ao ler arquivo")}
                
            extracted_text = parse_result.get("raw_text", str(parse_result))
            doc_type = parse_result.get("document_type", "geral").lower()
            traveler = parse_result.get("primary_traveler_name")
            location = parse_result.get("destination") or parse_result.get("venue")
            date = parse_result.get("start_date")
            is_travel = parse_result.get("is_travel_content", True)

            # C. Trip Matching / Creation
            trip = None
            if not dry_run:
                trip = self.trip_svc.add_trip_from_doc(sender_number, parse_result)
                if trip: user_svc.set_active_trip(sender_number, trip["id"])
            else:
                trip = self.trip_svc.extract_trip_data(parse_result)
            
            active_trip_id = user_svc.get_active_trip(sender_number)

            # D. [STRICT DEDUPLICATION] (Adendo Crítico)
            if not dry_run and is_travel:
                duplicate_found = False
                for doc in self.rag_svc.documents:
                    m = doc["metadata"]
                    if m.get("trip_id") == active_trip_id or m.get("thread_id") == sender_number:
                        if m.get("document_type") == doc_type:
                            obj_traveler = (m.get("primary_traveler_name") == traveler) if traveler and m.get("primary_traveler_name") else True
                            obj_date = (m.get("start_date") == date) if date and m.get("start_date") else True
                            if obj_traveler and obj_date:
                                duplicate_found = True
                                break
                
                if duplicate_found:
                    logger.info(f"♻️ Duplicata objetiva detectada para {doc_type}")
                    return {
                        "success": True, 
                        "status": "conflict", 
                        "document_type": doc_type,
                        "traveler": traveler,
                        "date": date,
                        "filename": filename,
                        "extracted_data": parse_result,
                        "text": extracted_text,
                        "drive_link": drive_link
                    }

            # E. Indexação RAG
            if not dry_run and is_travel:
                metadata = {
                    "filename": filename,
                    "thread_id": sender_number,
                    "trip_id": active_trip_id,
                    "document_type": doc_type,
                    "primary_traveler_name": traveler,
                    "start_date": date,
                    "drive_link": drive_link,
                    "segment_info": parse_result.get("segment_info")
                }
                self.rag_svc.delete_documents_by_type(sender_number, doc_type, active_trip_id, filename)
                self.index_chunks(extracted_text, metadata)

            # F. Matches de Terceiros
            trip_match = None
            if trip:
                similar = self.trip_svc.find_similar_trips(sender_number, trip.get("destination", ""), trip.get("start_date", ""))
                if similar:
                    trip_match = {
                        "host_user_id": similar["host_user_id"],
                        "trip_id": similar["trip"]["id"],
                        "destination": similar["trip"]["destination"],
                        "start_date": similar["trip"]["start_date"]
                    }

            return {
                "success": True,
                "filename": filename,
                "document_type": doc_type,
                "is_travel_content": is_travel,
                "trip_match": trip_match,
                "status": "success" if is_travel else "irrelevant",
                "drive_link": drive_link,
                "text": extracted_text,
                "metadata": metadata if is_travel else {
                    "filename": filename,
                    "thread_id": sender_number,
                    "trip_id": active_trip_id,
                    "document_type": doc_type,
                    "drive_link": drive_link
                }
            }
        except Exception as e:
            logger.error(f"❌ Erro no processamento: {e}")
            return {"success": False, "error": str(e)}

    def index_chunks(self, text: str, metadata: Dict):
        """Divide o texto em chunks e indexa no RAG usando batching para performance."""
        chunk_size = 4000
        overlap = 200
        docs_to_index = []
        
        if len(text) > chunk_size:
            for i in range(0, len(text), chunk_size - overlap):
                chunk = text[i:i + chunk_size]
                docs_to_index.append({"text": chunk, "metadata": metadata})
        else:
            docs_to_index.append({"text": text, "metadata": metadata})
            
        # Indexa tudo de uma vez para evitar múltiplas gravações em disco
        self.rag_svc.add_documents_batch(docs_to_index)
