"""
Document Parser - Parser genérico para documentos diversos
"""

from app.parsers.base_parser import BaseParser
from app.services.openai_service import OpenAIService
from loguru import logger
from typing import Dict, Any

class DocumentParser(BaseParser):
    """Parser genérico para qualquer tipo de documento"""
    
    def __init__(self, openai_svc: OpenAIService = None):
        """Inicializa o parser genérico com injeção de dependência"""
        super().__init__(openai_svc)
        self.supported_formats = ['pdf', 'txt']
        logger.info("✅ DocumentParser inicializado")
    
    def parse(self, file_content: bytes, filename: str, document_type: str = "documento genérico") -> Dict[str, Any]:
        """Extrai informações de um documento genérico"""
        logger.info(f"📄 Parseando documento: {filename} ({document_type})")
        
        if filename.lower().endswith('.pdf'):
            text = self.extract_text_from_pdf(file_content)
        elif filename.lower().endswith('.txt'):
            text = file_content.decode('utf-8', errors='ignore')
        else:
            logger.warning(f"Formato {filename} requer OCR ou Vision API")
            text = "Imagem de documento (OCR pendente)"
        
        if not self.is_valid_text(text):
            return {
                "success": False,
                "error": "Texto insuficiente, formato inválido ou requer OCR (envie PDF ou TXT).",
                "document_type": document_type,
                "filename": filename
            }
        
        if not self.openai_svc:
            return {
                "success": False,
                "error": "OpenAI Service não configurado",
                "document_type": document_type
            }
        
        result = self.openai_svc.analyze_document(text, document_type)
        result["document_type"] = document_type
        result["filename"] = filename
        result["raw_text"] = text[:500]
        
        logger.info("✅ Documento parseado com sucesso")
        return result
