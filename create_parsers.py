"""
TravelCompanion AI - Criação Automática de Parsers
Executa: python create_parsers.py
"""

import os
from pathlib import Path

FILES = {}

# ============================================================
# BASE PARSER
# ============================================================
FILES["app/parsers/base_parser.py"] = '''"""
Base Parser - Classe abstrata para todos os parsers
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from loguru import logger
import PyPDF2
import io

class BaseParser(ABC):
    """Classe base para todos os parsers de documentos"""
    
    def __init__(self, openai_svc=None):
        """Inicializa o parser com injeção de dependência opcional"""
        self.supported_formats = []
        self.openai_svc = openai_svc
        
    @abstractmethod
    def parse(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Método abstrato que cada parser deve implementar"""
        pass
    
    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extrai texto de um PDF"""
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\\n"
            
            logger.debug(f"Texto extraído do PDF: {len(text)} caracteres")
            return text.strip()
            
        except Exception as e:
            logger.error(f"Erro ao extrair texto do PDF: {e}")
            return ""
    
    def is_supported(self, filename: str) -> bool:
        """Verifica se o formato do arquivo é suportado"""
        extension = filename.lower().split('.')[-1]
        return extension in self.supported_formats
    
    def is_valid_text(self, text: str) -> bool:
        """Verifica se o texto extraído é válido para análise pela IA"""
        if not text or len(text.strip()) < 10:
            return False
        
        # Blindagem contra placeholders de OCR
        invalid_phrases = [
            "OCR pendente",
            "Imagem de",
            "pending OCR",
            "Image of"
        ]
        
        text_lower = text.lower()
        return not any(phrase.lower() in text_lower for phrase in invalid_phrases)
'''

# ============================================================
# FLIGHT PARSER
# ============================================================
FILES["app/parsers/flight_parser.py"] = '''"""
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
'''

# ============================================================
# HOTEL PARSER
# ============================================================
FILES["app/parsers/hotel_parser.py"] = '''"""
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
'''

# ============================================================
# DOCUMENT PARSER
# ============================================================
FILES["app/parsers/document_parser.py"] = '''"""
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
'''

# ============================================================
# PARSER FACTORY
# ============================================================
FILES["app/parsers/parser_factory.py"] = '''"""
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
        """Inicializa a factory com uma ÚNICA instância do OpenAI Service"""
        # Otimização: Uma única instância compartilhada economiza memória
        self.openai_svc = OpenAIService()
        
        # Injeção de dependência: todos os parsers usam o mesmo service
        self.flight_parser = FlightParser(openai_svc=self.openai_svc)
        self.hotel_parser = HotelParser(openai_svc=self.openai_svc)
        self.document_parser = DocumentParser(openai_svc=self.openai_svc)
        
        logger.info("✅ ParserFactory inicializado (OpenAI Service compartilhado)")
    
    def auto_parse(self, file_content: bytes, filename: str, document_hint: str = None) -> Dict[str, Any]:
        """Detecta automaticamente o tipo de documento e usa o parser adequado"""
        logger.info(f"🔍 Auto-detectando tipo de documento: {filename}")
        
        filename_lower = filename.lower()
        hint_lower = (document_hint or "").lower()
        
        if any(word in filename_lower or word in hint_lower for word in ['flight', 'ticket', 'boarding', 'voo', 'passagem']):
            logger.info("✈️ Detectado: Passagem aérea")
            return self.flight_parser.parse(file_content, filename)
        
        elif any(word in filename_lower or word in hint_lower for word in ['hotel', 'reservation', 'booking', 'hospedagem', 'reserva']):
            logger.info("🏨 Detectado: Reserva de hotel")
            return self.hotel_parser.parse(file_content, filename)
        
        else:
            logger.info("📄 Usando parser genérico")
            return self.document_parser.parse(file_content, filename, document_hint or "documento de viagem")
'''

# ============================================================
# __INIT__
# ============================================================
FILES["app/parsers/__init__.py"] = '''"""Parsers - Extração de dados de documentos"""

from .base_parser import BaseParser
from .flight_parser import FlightParser
from .hotel_parser import HotelParser
from .document_parser import DocumentParser
from .parser_factory import ParserFactory

__all__ = [
    "BaseParser",
    "FlightParser",
    "HotelParser",
    "DocumentParser",
    "ParserFactory"
]
'''

def create_parsers():
    """Cria todos os arquivos de parsers"""
    
    print("=" * 70)
    print("📄 CRIANDO PARSERS - EXTRAÇÃO DE DADOS DE DOCUMENTOS")
    print("=" * 70)
    print()
    
    for filepath, content in FILES.items():
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"   ✅ {filepath}")
    
    print()
    print("=" * 70)
    print("✅ PARSERS CRIADOS COM SUCESSO E BLINDADOS!")
    print("=" * 70)
    print()
    print("📋 Melhorias aplicadas:")
    print("   ✅ Injeção de dependência (1 instância OpenAI)")
    print("   ✅ Validação centralizada de texto is_valid_text()")
    print("   ✅ Encoding de logs consertado (Fim do Mojibake)")
    print("   ✅ Type Hinting restaurado para IDEs")
    print()

if __name__ == "__main__":
    create_parsers()