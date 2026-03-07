"""
Car Rental Parser - Extrai informações de contratos de locação de veículos
"""

from app.parsers.base_parser import BaseParser
from app.services.openai_service import OpenAIService
from loguru import logger
from typing import Dict, Any

class CarRentalParser(BaseParser):
    """Parser especializado em contratos e vouchers de locação de carro"""
    
    def __init__(self, openai_svc: OpenAIService = None):
        super().__init__(openai_svc)
        logger.info("✅ CarRentalParser inicializado (Com suporte a OCR)")
    
    def parse(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        logger.info(f"🚗 Parseando contrato de locação de carro: {filename}")
        
        text = self.extract_text(file_content, filename)
        
        if not self.is_valid_text(text):
            return {
                "success": False,
                "error": "Não foi possível extrair texto legível do contrato de locação.",
                "document_type": "car_rental",
                "filename": filename
            }
        
        if not self.openai_svc:
            return {"success": False, "error": "OpenAI Service não configurado"}
        
        # Prompt especializado para extrair campos de locação de carro
        context_hint = (
            "locação de carro / car rental. "
            "Extraia obrigatoriamente: empresa locadora (ex: Localiza, Hertz, Avis, Movida), "
            "número da reserva/voucher, local e terminal de RETIRADA do carro, "
            "local de DEVOLUÇÃO, data e hora de retirada, data e hora de devolução, "
            "categoria ou modelo do veículo, nome do condutor principal, "
            "e se inclui ou não seguro. "
            "BUSQUE TAMBÉM: Informações de shuttle (traslado) e o PONTO DE ENCONTRO exato no aeroporto. "
            "Os campos 'pickup_location', 'pickup_terminal' e 'meeting_point' são CRÍTICOS para o guia de chegada."
        )
        
        result = self.openai_svc.analyze_document(text, context_hint)
        result["document_type"] = "car_rental"
        result["filename"] = filename
        result["raw_text"] = text
        result["is_travel_content"] = True
        
        logger.info("✅ Contrato de locação parseado com sucesso!")
        return result
