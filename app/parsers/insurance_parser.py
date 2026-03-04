"""
Insurance Parser - Extrai informações de apólices de seguro viagem
"""

from app.parsers.base_parser import BaseParser
from app.services.openai_service import OpenAIService
from loguru import logger
from typing import Dict, Any

class InsuranceParser(BaseParser):
    """Parser especializado em documentos de seguro viagem"""
    
    def __init__(self, openai_svc: OpenAIService = None):
        super().__init__(openai_svc)
        logger.info("✅ InsuranceParser inicializado (Com suporte a OCR)")
    
    def parse(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        logger.info(f"🛡️ Parseando seguro de viagem: {filename}")
        
        text = self.extract_text(file_content, filename)
        
        if not self.is_valid_text(text):
            return {
                "success": False,
                "error": "Não foi possível extrair texto legível da apólice de seguro.",
                "document_type": "seguro_viagem",
                "filename": filename
            }
        
        if not self.openai_svc:
            return {"success": False, "error": "OpenAI Service não configurado"}
        
        # Prompt especializado para extrair campos de seguro de viagem
        context_hint = (
            "apólice de seguro de viagem / travel insurance. "
            "Extraia obrigatoriamente: número da apólice, seguradora, "
            "nome do(s) segurado(s), período de cobertura (data início e fim), "
            "destino coberto, coberturas principais (médica, cancelamento, bagagem, etc.), "
            "valor da cobertura médica em USD ou EUR (muito importante para emergências), "
            "número de telefone de EMERGÊNCIA 24h da seguradora (campo 'emergency_phone' — CRÍTICO), "
            "e e-mail de contato. "
            "Esse seguro é essencial para guiar o usuário em caso de emergência no exterior."
        )
        
        result = self.openai_svc.analyze_document(text, context_hint)
        result["document_type"] = "seguro_viagem"
        result["filename"] = filename
        result["raw_text"] = text
        result["is_travel_content"] = True
        
        logger.info("✅ Apólice de seguro parseada com sucesso!")
        return result
