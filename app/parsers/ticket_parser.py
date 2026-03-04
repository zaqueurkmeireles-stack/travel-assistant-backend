"""
Ticket Parser - Extrai informações de ingressos de shows, eventos e parques
"""

from app.parsers.base_parser import BaseParser
from app.services.openai_service import OpenAIService
from loguru import logger
from typing import Dict, Any

class TicketParser(BaseParser):
    """Parser especializado em ingressos de shows, eventos, parques e esportes"""
    
    def __init__(self, openai_svc: OpenAIService = None):
        super().__init__(openai_svc)
        logger.info("✅ TicketParser inicializado (Com suporte a OCR)")
    
    def parse(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        logger.info(f"🎟️ Parseando ingresso de evento: {filename}")
        
        text = self.extract_text(file_content, filename)
        
        if not self.is_valid_text(text):
            return {
                "success": False,
                "error": "Não foi possível extrair texto legível do ingresso.",
                "document_type": "ingresso",
                "filename": filename
            }
        
        if not self.openai_svc:
            return {"success": False, "error": "OpenAI Service não configurado"}
        
        # Prompt especializado para extrair campos de ingresso de evento
        context_hint = (
            "ingresso de evento / event ticket. "
            "Extraia obrigatoriamente: nome do evento (ex: 'F1 Grand Prix', 'Show Taylor Swift', 'Disney Magic Kingdom'), "
            "data e hora do evento, nome do local/venue, "
            "portão/gate/entrada (campo 'gate' — CRÍTICO para guia no local), "
            "setor ou categoria do assento (ex: Camarote, Pista, Tribuna Norte), "
            "número do assento ou área, nome do(s) participante(s), "
            "código do ingresso ou QR Code (campo 'ticket_code'), "
            "e se é ingresso para parque temático (sim/não). "
            "O portão de entrada é fundamental para o Seven guiar o usuário ao chegar no evento."
        )
        
        result = self.openai_svc.analyze_document(text, context_hint)
        result["document_type"] = "ingresso"
        result["filename"] = filename
        result["raw_text"] = text
        result["is_travel_content"] = True
        
        logger.info("✅ Ingresso parseado com sucesso!")
        return result
