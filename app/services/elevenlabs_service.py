"""
ElevenLabs Service - Conversão de texto em áudio para mensagens de voz
"""

import requests
from app.config import settings
from loguru import logger
from typing import Optional

class ElevenLabsService:
    """Service para integração com ElevenLabs (Voz da IA)"""
    
    def __init__(self):
        """Inicializa o service"""
        self.api_key = settings.ELEVENLABS_API_KEY
        self.base_url = "https://api.elevenlabs.io/v1"
        
        if not self.api_key:
            logger.warning("⚠️ ElevenLabs API key não configurada.")
        else:
            logger.info("✅ ElevenLabs Service inicializado")
            
    def text_to_speech(self, text: str, voice_id: str = "pNInz6obpgH9P3OhJAgv") -> Optional[bytes]:
        """Converte texto em áudio (MP3)"""
        if not self.api_key:
            return None
            
        try:
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                logger.info("✅ Áudio gerado com sucesso via ElevenLabs")
                return response.content
            else:
                logger.error(f"Erro no ElevenLabs: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao converter texto em áudio: {e}")
            return None
