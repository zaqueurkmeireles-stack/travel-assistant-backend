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
        """Extrai texto de um PDF (tenta texto nativo primeiro, depois OCR)"""
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            
            # Se o PDF for só uma imagem escaneada (boarding pass etc), OCR real
            if len(text.strip()) < 20:
                logger.info("📷 PDF parece ser baseado em imagem (ex: boarding pass). Iniciando OCR via pdf2image...")
                try:
                    from pdf2image import convert_from_bytes
                    images = convert_from_bytes(file_content, dpi=200)
                    ocr_text = ""
                    for img in images:
                        page_text = pytesseract.image_to_string(img, lang='por+eng')
                        ocr_text += page_text + "\n"
                    
                    if ocr_text.strip():
                        logger.info(f"✅ OCR concluído: {len(ocr_text)} caracteres extraídos de {len(images)} página(s)")
                        return ocr_text.strip()
                    else:
                        logger.warning("⚠️ OCR não extraiu texto. PDF pode ser muito complexo ou corrompido.")
                except ImportError:
                    logger.error("❌ pdf2image não instalado. Adicione 'pdf2image' ao requirements.txt")
                except Exception as ocr_err:
                    logger.error(f"❌ Erro no OCR do PDF: {ocr_err}")
            
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
