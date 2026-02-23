"""
Parser Factory - Seleciona o parser adequado automaticamente
"""

from app.parsers.flight_parser import FlightParser
from app.parsers.hotel_parser import HotelParser
from app.parsers.document_parser import DocumentParser
from app.services.openai_service import OpenAIService
from loguru import logger
from typing import Dict, Any

class ParserFactory:
    """Factory para selecionar o parser correto baseado no tipo de documento"""
    
    def __init__(self):
        self.openai_svc = OpenAIService()
        self.flight_parser = FlightParser(openai_svc=self.openai_svc)
        self.hotel_parser = HotelParser(openai_svc=self.openai_svc)
        self.document_parser = DocumentParser(openai_svc=self.openai_svc)
        logger.info("✅ ParserFactory inicializado")
    
    def auto_parse(self, file_content: bytes, filename: str, document_hint: str = None) -> Dict[str, Any]:
        logger.info(f"🔍 Auto-detectando tipo de documento: {filename}")
        
        filename_lower = filename.lower()
        hint_lower = (document_hint or "").lower()
        
        if any(word in filename_lower or word in hint_lower for word in ['flight', 'ticket', 'boarding', 'voo', 'passagem']):
            return self.flight_parser.parse(file_content, filename)
        
        elif any(word in filename_lower or word in hint_lower for word in ['hotel', 'reservation', 'booking', 'hospedagem', 'reserva']):
            return self.hotel_parser.parse(file_content, filename)
        
        else:
            return self.document_parser.parse(file_content, filename, document_hint or "documento de viagem")
