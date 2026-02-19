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
        """Inicializa o parser de hotéis com injeção de dependência"""
        super().__init__(openai_svc)
        self.supported_formats = ['pdf']
        logger.info("✅ HotelParser inicializado")
    
    def parse(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Extrai informações de uma reserva de hotel"""
        logger.info(f"🏨 Parseando reserva de hotel: {filename}")
        
        if filename.lower().endswith('.pdf'):
            text = self.extract_text_from_pdf(file_content)
        else:
            logger.warning(f"Formato {filename} requer OCR ou Vision API")
            text = "Imagem de reserva (OCR pendente)"
        
        if not self.is_valid_text(text):
            return {
                "success": False,
                "error": "Texto insuficiente, formato inválido ou requer OCR (envie PDF).",
                "document_type": "hotel_reservation",
                "filename": filename
            }
        
        if not self.openai_svc:
            return {
                "success": False,
                "error": "OpenAI Service não configurado",
                "document_type": "hotel_reservation"
            }
        
        result = self.openai_svc.analyze_document(text, "reserva de hotel")
        result["document_type"] = "hotel_reservation"
        result["filename"] = filename
        
        logger.info(f"✅ Reserva parseada: {result.get('hotel_name', 'N/A')}")
        return result
