"""
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
                    text += extracted + "\n"
            
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
