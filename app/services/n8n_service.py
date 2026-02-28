"""
N8N Service - Integração com o fluxo do n8n (WhatsApp + Chatwoot)
"""

import requests
from loguru import logger
from typing import Dict, Any

class N8nService:
    """Service para enviar mensagens de volta para o usuário através do n8n"""
    
    def __init__(self):
        # A URL do webhook do n8n que vai RECEBER as respostas da nossa IA
        # Vamos configurar isso no arquivo .env depois
        import os
        self.webhook_url = os.getenv("N8N_WEBHOOK_URL_OUTPUT", "")
        
        if not self.webhook_url:
            logger.warning("⚠️ URL do Webhook do n8n não configurada (modo simulação)")
        else:
            logger.info("✅ N8n Service inicializado")
            
    def enviar_resposta_usuario(self, numero_usuario: str, mensagem: str) -> bool:
        """Envia a resposta gerada pela IA de volta para o n8n entregar no WhatsApp"""
        if not numero_usuario or numero_usuario.strip() == "":
            logger.warning("⚠️ Tentativa de enviar resposta para um número vazio. Abortando.")
            return False

        if not self.webhook_url:
            logger.info(f"[SIMULADO - N8N] Para {numero_usuario}: {mensagem}")
            return True
            
        try:
            payload = {
                "telefone": numero_usuario,
                "mensagem": mensagem,
                "origem": "ia_travel_companion"
            }
            
            logger.info(f"📤 Chamando n8n em: {self.webhook_url}")
            response = requests.post(self.webhook_url, json=payload, timeout=15)
            
            if response.status_code == 200:
                logger.info(f"✅ Resposta enviada para o n8n (Destino: {numero_usuario})")
                return True
            else:
                logger.error(f"❌ Erro ao enviar para o n8n. Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro de conexão com o n8n: {e}")
            return False

    def broadcast_to_all(self, mensagem: str, user_ids: list) -> dict:
        """Envia uma mensagem para uma lista de usuários"""
        results = {"total": len(user_ids), "success": 0, "failed": 0}
        for uid in user_ids:
            if self.enviar_resposta_usuario(uid, mensagem):
                results["success"] += 1
            else:
                results["failed"] += 1
        return results
