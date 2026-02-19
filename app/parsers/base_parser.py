"""
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
                text += page.extract_text() + "\n"
            
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
