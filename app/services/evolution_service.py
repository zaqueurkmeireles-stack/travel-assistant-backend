"""
Evolution API Service - Integração com os endpoints REST da Evolution API.
Usado para baixar mídias, gerenciar instâncias e consultas avançadas.
"""

import requests
import base64
from loguru import logger
from app.config import settings

class EvolutionService:
    """Service para interagir com a API REST da Evolution"""
    
    def __init__(self):
        # A URL base da Evolution API (ex: http://evolution-api:8080)
        # E a API Key global ou da instância
        self.base_url = settings.EVOLUTION_API_URL or "http://localhost:8080"
        self.api_key = settings.EVOLUTION_API_KEY
        self.instance_name = settings.EVOLUTION_INSTANCE_NAME or "Seven_Assistant"
        
        if not self.api_key:
            logger.warning("⚠️ EVOLUTION_API_KEY não configurada. Endpoints REST falharão.")
            
    def get_base64_media(self, message_id: str, remote_jid: str = None) -> str:
        """
        Busca o conteúdo Base64 de uma mensagem de mídia específica via API REST.
        Útil quando o webhook não envia o base64 (comum em encaminhamentos).
        """
        if not message_id:
            return ""
            
        try:
            # Endpoint para converter mensagem em Base64
            # Documentação Evolution: POST /chat/getBase64FromMediaMessage/{instance}
            url = f"{self.base_url}/chat/getBase64FromMediaMessage/{self.instance_name}"
            
            headers = {
                "apikey": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "messageKey": {
                    "id": message_id
                }
            }
            if remote_jid:
                payload["messageKey"]["remoteJid"] = remote_jid
            
            logger.info(f"📥 Solicitando Base64 para mensagem {message_id} via REST API: {url}")
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                # O retorno costuma ser {"base64": "..."} ou similar
                b64 = data.get("base64") or data.get("image") or data.get("video") or data.get("document")
                if b64:
                    logger.info(f"✅ Base64 recuperado com sucesso para {message_id}")
                    return b64
                
            logger.error(f"❌ Falha ao recuperar Base64. Status: {response.status_code} | Resposta: {response.text[:200]}")
            return ""
            
        except Exception as e:
            logger.error(f"❌ Erro crítico ao chamar Evolution API: {e}")
            return ""

    def get_message_content(self, message_id: str, remote_jid: str = None) -> bytes:
        """Retorna o conteúdo binário puro (decodificado) da mídia"""
        b64_str = self.get_base64_media(message_id, remote_jid)
        if not b64_str:
            return None
            
        try:
            # Remover prefixos data:image/png;base64, se houver
            if "," in b64_str:
                b64_str = b64_str.split(",")[1]
            return base64.b64decode(b64_str)
        except Exception as e:
            logger.error(f"❌ Erro ao decodificar Base64 recuperado: {e}")
            return None
