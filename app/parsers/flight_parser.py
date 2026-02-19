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
        """Inicializa o parser de voos com injeção de dependência"""
        super().__init__(openai_svc)
        # Removido suporte falso a imagens por enquanto (OCR pendente)
        self.supported_formats = ['pdf']
        logger.info("✅ FlightParser inicializado")
    
    def parse(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Extrai informações de uma passagem aérea"""
        logger.info(f"📄 Parseando passagem aérea: {filename}")
        
        if filename.lower().endswith('.pdf'):
            text = self.extract_text_from_pdf(file_content)
        else:
            logger.warning(f"Formato {filename} requer OCR ou Vision API")
            text = "Imagem de passagem (OCR pendente)"
        
        # Validação blindada herdada do BaseParser
        if not self.is_valid_text(text):
            return {
                "success": False,
                "error": "Texto insuficiente, formato inválido ou requer OCR (envie PDF).",
                "document_type": "flight_ticket",
                "filename": filename
            }
        
        if not self.openai_svc:
            return {
                "success": False,
                "error": "OpenAI Service não configurado",
                "document_type": "flight_ticket"
            }
        
        result = self.openai_svc.analyze_document(text, "passagem aérea")
        result["document_type"] = "flight_ticket"
        result["filename"] = filename
        
        logger.info(f"✅ Passagem parseada: {result.get('flight_number', 'N/A')}")
        return result
