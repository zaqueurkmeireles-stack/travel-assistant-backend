"""
WhatsApp Service - Envio de mensagens via WhatsApp Business API
"""

import requests
from app.config import settings
from loguru import logger
from typing import Optional

class WhatsAppService:
    """Service para envio de mensagens WhatsApp"""
    
    def __init__(self):
        """Inicializa o service"""
        self.token = settings.WHATSAPP_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.base_url = "https://graph.facebook.com/v18.0"
        
        if not self.token or not self.phone_number_id:
            logger.warning("⚠️ WhatsApp não configurado (modo simulação)")
        else:
            logger.info("✅ WhatsApp Service inicializado")
    
    def send_message(self, to: str, message: str) -> bool:
        """Envia mensagem de texto"""
        if not self.token or not self.phone_number_id:
            logger.info(f"[SIMULADO] Mensagem para {to}: {message}")
            return True
        
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            data = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": message}
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=15)
            
            if response.status_code == 200:
                logger.info(f"✅ Mensagem enviada para {to}")
                return True
            else:
                logger.error(f"Erro ao enviar mensagem: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Erro no WhatsAppService: {e}")
            return False
    
    def send_location(self, to: str, latitude: float, longitude: float, name: str, address: str) -> bool:
        """Envia localização"""
        if not self.token or not self.phone_number_id:
            logger.info(f"[SIMULADO] Localização para {to}: {name} ({latitude}, {longitude})")
            return True
        
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            data = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "location",
                "location": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "name": name,
                    "address": address
                }
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=15)
            
            if response.status_code == 200:
                logger.info(f"✅ Localização enviada para {to}")
                return True
            else:
                logger.error(f"Erro ao enviar localização: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao enviar localização: {e}")
            return False
