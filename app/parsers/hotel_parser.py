"""
Hotel Parser - Extrai informações de reservas de hotel
"""

from app.parsers.base_parser import BaseParser
from app.services.openai_service import OpenAIService
from loguru import logger
from typing import Dict, Any

class HotelParser(BaseParser):
    """Parser especializado em reservas de hotel"""
    
    def __init__(self, openai_svc: OpenAIService = None):
        super().__init__(openai_svc)
        logger.info("✅ HotelParser inicializado (Com suporte a OCR)")
    
    def parse(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        logger.info(f"🏨 Parseando reserva de hotel: {filename}")
        
        text = self.extract_text(file_content, filename)
        
        if not self.is_valid_text(text):
            return {
                "success": False,
                "error": "Não foi possível extrair texto legível da imagem ou PDF.",
                "document_type": "hotel_reservation",
                "filename": filename
            }
        
        if not self.openai_svc:
            return {"success": False, "error": "OpenAI Service não configurado"}
        
        result = self.openai_svc.analyze_document(text, "reserva de hotel")
        result["document_type"] = "hotel_reservation"
        result["filename"] = filename
        
        logger.info(f"✅ Reserva parseada com sucesso!")
        return result
