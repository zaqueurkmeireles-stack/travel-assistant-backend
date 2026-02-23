"""
Flight Parser - Extrai informações de bilhetes aéreos
"""

from app.parsers.base_parser import BaseParser
from app.services.openai_service import OpenAIService
from loguru import logger
from typing import Dict, Any

class FlightParser(BaseParser):
    """Parser especializado em passagens aéreas"""
    
    def __init__(self, openai_svc: OpenAIService = None):
        super().__init__(openai_svc)
        logger.info("✅ FlightParser inicializado (Com suporte a OCR)")
    
    def parse(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        logger.info(f"📄 Parseando passagem aérea: {filename}")
        
        text = self.extract_text(file_content, filename)
        
        if not self.is_valid_text(text):
            return {
                "success": False,
                "error": "Não foi possível extrair texto legível da imagem ou PDF.",
                "document_type": "flight_ticket",
                "filename": filename
            }
        
        if not self.openai_svc:
            return {"success": False, "error": "OpenAI Service não configurado"}
        
        result = self.openai_svc.analyze_document(text, "passagem aérea")
        result["document_type"] = "flight_ticket"
        result["filename"] = filename
        
        logger.info(f"✅ Passagem parseada com sucesso!")
        return result
