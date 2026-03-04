"""
Parser Factory - Seleciona o parser adequado automaticamente
"""

from app.parsers.flight_parser import FlightParser
from app.parsers.hotel_parser import HotelParser
from app.parsers.document_parser import DocumentParser
from app.parsers.car_rental_parser import CarRentalParser
from app.parsers.insurance_parser import InsuranceParser
from app.parsers.ticket_parser import TicketParser
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
        self.car_rental_parser = CarRentalParser(openai_svc=self.openai_svc)
        self.insurance_parser = InsuranceParser(openai_svc=self.openai_svc)
        self.ticket_parser = TicketParser(openai_svc=self.openai_svc)
        logger.info("✅ ParserFactory inicializado (6 parsers especializados ativos)")
    
    def auto_parse(self, file_content: bytes, filename: str, document_hint: str = None) -> Dict[str, Any]:
        logger.info(f"🔍 Auto-detectando tipo de documento: {filename}")
        
        filename_lower = filename.lower()
        hint_lower = (document_hint or "").lower()
        combined = filename_lower + " " + hint_lower

        # 1. Passagem Aérea
        if any(w in combined for w in ['flight', 'boarding', 'voo', 'passagem', 'airway', 'aereo', 'eticket', 'e-ticket']):
            return self.flight_parser.parse(file_content, filename)
        
        # 2. Hotel / Hospedagem
        if any(w in combined for w in ['hotel', 'reservation', 'booking', 'hospedagem', 'reserva', 'airbnb', 'hostel', 'pousada']):
            return self.hotel_parser.parse(file_content, filename)
        
        # 3. Locação de Carro (verificar ANTES dos genéricos para não cair no DocumentParser)
        if any(w in combined for w in ['car', 'carro', 'locacao', 'aluguel', 'rental', 'hertz', 'localiza', 'movida', 'avis', 'budget', 'sixt', 'europcar', 'unidas']):
            return self.car_rental_parser.parse(file_content, filename)
        
        # 4. Seguro de Viagem
        if any(w in combined for w in ['seguro', 'insurance', 'apolice', 'cobertura', 'assist', 'seguros']):
            return self.insurance_parser.parse(file_content, filename)
        
        # 5. Ingresso / Ticket de Evento ou Parque
        if any(w in combined for w in ['ingresso', 'ticket', 'show', 'evento', 'concert', 'festival', 'f1', 'formula', 'disney', 'universal', 'park', 'parque', 'soccer', 'futebol', 'stadium']):
            return self.ticket_parser.parse(file_content, filename)
        
        # 6. Fallback genérico para roteiros, documentos de viagem diversos
        return self.document_parser.parse(file_content, filename, document_hint or "documento de viagem")
