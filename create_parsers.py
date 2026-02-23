"""
TravelCompanion AI - Criação Automática de Parsers
Executa: python create_parsers.py
"""

import os
from pathlib import Path

FILES = {}

# ============================================================
# BASE PARSER (AGORA COM OCR ATIVADO!)
# ============================================================
FILES["app/parsers/base_parser.py"] = '''"""
Base Parser - Classe abstrata para todos os parsers
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from loguru import logger
import PyPDF2
import io
import pytesseract
from PIL import Image

class BaseParser(ABC):
    """Classe base para todos os parsers de documentos"""
    
    def __init__(self, openai_svc=None):
        """Inicializa o parser com injeção de dependência opcional"""
        self.supported_formats = ['pdf', 'png', 'jpg', 'jpeg']
        self.openai_svc = openai_svc
        
    @abstractmethod
    def parse(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Método abstrato que cada parser deve implementar"""
        pass
    
    def extract_text(self, file_content: bytes, filename: str) -> str:
        """Decide qual método usar baseado na extensão do arquivo"""
        ext = filename.lower().split('.')[-1]
        
        if ext == 'pdf':
            return self.extract_text_from_pdf(file_content)
        elif ext in ['png', 'jpg', 'jpeg']:
            return self.extract_text_from_image(file_content)
        else:
            logger.warning(f"Formato não suportado para extração: {ext}")
            return ""

    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extrai texto de um PDF (tenta texto nativo primeiro)"""
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\\n"
            
            # Se o PDF for só uma imagem escaneada, o texto nativo virá vazio
            if len(text.strip()) < 20:
                logger.info("PDF parece ser escaneado. Tentando OCR (em breve via conversão de página)...")
                # Nota: Para OCR completo em PDF, precisaríamos do pdf2image. 
                # Por enquanto, focamos em imagens diretas.
                
            logger.debug(f"Texto extraído do PDF: {len(text)} caracteres")
            return text.strip()
            
        except Exception as e:
            logger.error(f"Erro ao extrair texto do PDF: {e}")
            return ""

    def extract_text_from_image(self, file_content: bytes) -> str:
        """Extrai texto de uma imagem usando Tesseract OCR"""
        try:
            logger.info("🔍 Iniciando extração de texto via OCR (Tesseract)...")
            image = Image.open(io.BytesIO(file_content))
            
            # Executa o OCR (assumindo que o Tesseract está instalado no sistema)
            text = pytesseract.image_to_string(image, lang='por+eng')
            
            logger.debug(f"Texto extraído via OCR: {len(text)} caracteres")
            return text.strip()
            
        except Exception as e:
            logger.error(f"❌ Erro no OCR: {e}. Verifique se o Tesseract está instalado no SO.")
            return ""
    
    def is_supported(self, filename: str) -> bool:
        """Verifica se o formato do arquivo é suportado"""
        extension = filename.lower().split('.')[-1]
        return extension in self.supported_formats
    
    def is_valid_text(self, text: str) -> bool:
        """Verifica se o texto extraído é válido para análise pela IA"""
        if not text or len(text.strip()) < 10:
            return False
        return True
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
        super().__init__(openai_svc)
        logger.info("✅ HotelParser inicializado (Com suporte a OCR)")
    
    def parse(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        logger.info(f"🏨 Parseando reserva de hotel: {filename}")
        
        text = self.extract_text(file_content, filename)
        
        if not self.is_valid_text(text):
            return {
                "success": False,
                "error": "Não foi possível extrair texto legível da imagem ou PDF.",
                "document_type": "hotel_reservation",
                "filename": filename
            }
        
        if not self.openai_svc:
            return {"success": False, "error": "OpenAI Service não configurado"}
        
        result = self.openai_svc.analyze_document(text, "reserva de hotel")
        result["document_type"] = "hotel_reservation"
        result["filename"] = filename
        
        logger.info(f"✅ Reserva parseada com sucesso!")
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
    print("📄 CRIANDO PARSERS - COM SUPORTE A OCR (IMAGENS)")
    print("=" * 70)
    print()
    
    for filepath, content in FILES.items():
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"   ✅ {filepath}")
    
    print()
    print("=" * 70)
    print("✅ PARSERS CRIADOS COM SUCESSO!")
    print("=" * 70)

if __name__ == "__main__":
    create_parsers()