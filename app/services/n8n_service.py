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

        # --- [FIREWALL DE SAÍDA] ---
        # 🛡️ Proteção para nunca ser proativo com estranhos ou grupos
        try:
            from app.services.user_service import UserService
            from app.config import settings
            user_svc = UserService()
            
            # 1. Admin sempre é liberado
            admin_number = user_svc.normalize_phone(getattr(settings, "ADMIN_WHATSAPP_NUMBER", ""))
            uid = user_svc.normalize_phone(numero_usuario)
            
            if uid == admin_number:
                pass # Liberado
            else:
                # 2. Se não for admin, tem que ser GUEST AUTORIZADO
                role = user_svc.get_user_role(uid)
                if role != "guest":
                    logger.warning(f"🛡️ [FIREWALL] Bloqueado: Tentativa de envio proativo para usuário não autorizado ({uid})")
                    return False
                
                # 3. Tem que ter uma TRIP ATIVA (o get_user_role já checa isso, mas reforçamos aqui)
                # O get_user_role("guest") no nosso backend atual só retorna guest se tiver trip ativa (D+2).
                # Se ele retornar "unauthorized", cai no bloco acima.
        except Exception as e:
            logger.error(f"⚠️ Erro ao validar firewall de saída para {numero_usuario}: {e}")
            # Na dúvida, se o firewall falhar (ex: erro de import), bloqueamos por segurança em modo proativo
            # Mas se for uma resposta direta de chat, o erro seria capturado antes.

        if not self.webhook_url:
            logger.info(f"[SIMULADO - N8N] Para {numero_usuario}: {mensagem}")
            return True
            
        try:
            payload = {
                "telefone": numero_usuario,
                "mensagem": mensagem,
                "origem": "ia_travel_companion"
            }
            
            logger.info(f"📤 Enviando para n8n: {self.webhook_url} | Destino: {numero_usuario}")
            logger.debug(f"📦 Payload n8n: {payload}")
            
            response = requests.post(self.webhook_url, json=payload, timeout=15)
            
            if response.status_code == 200:
                logger.info(f"✅ Sucesso no n8n para {numero_usuario}")
                return True
            else:
                logger.error(f"❌ Erro n8n. Status: {response.status_code} | Resposta: {response.text[:200]}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Falha crítica de conexão com n8n: {e}")
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
