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
        super().__init__(openai_svc)
        logger.info("✅ DocumentParser inicializado (Com suporte a OCR)")
    
    def parse(self, file_content: bytes, filename: str, document_type: str = "documento genérico") -> Dict[str, Any]:
        logger.info(f"📄 Parseando documento: {filename} ({document_type})")
        
        text = self.extract_text(file_content, filename)
        
        if not self.is_valid_text(text):
            return {
                "success": False,
                "error": "Não foi possível extrair texto legível do arquivo.",
                "document_type": document_type,
                "filename": filename
            }
        
        if not self.openai_svc:
            return {"success": False, "error": "OpenAI Service não configurado"}
        
        result = self.openai_svc.analyze_document(text, document_type)
        result["document_type"] = document_type
        result["filename"] = filename
        result["raw_text"] = text[:500]
        
        logger.info("✅ Documento parseado com sucesso")
        return result
