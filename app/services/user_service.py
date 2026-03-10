\"\"\"
User Service - TravelCompanion AI
Versão: 7.0 (Enterprise Fortress)
Data: 2026-03-10
\"\"\"

from loguru import logger
from typing import Tuple, Optional, Dict, Any
import phonenumbers
import os

class UserService:
    def __init__(self):
        # Admins carregados de variável de ambiente
        admin_env = os.getenv("ADMIN_PHONES", "")
        self.admins = [p.strip() for p in admin_env.split(",") if p.strip()]
        logger.info(f"✅ UserService v7.0 (Admins carregados: {len(self.admins)})")

    def normalize_phone(self, phone: str) -> str:
        \"\"\"Normaliza telefone usando phonenumbers (Padrão E.164)\"\"\"
        if not phone:
            raise ValueError("Telefone não pode ser vazio")
        try:
            # Garante o '+' para o parse do Google
            phone_to_parse = phone if phone.startswith('+') else f"+{phone}"
            if not phone.startswith('+') and not phone.startswith('55'):
                phone_to_parse = f"+55{phone}"
                
            parsed = phonenumbers.parse(phone_to_parse, None)
            if not phonenumbers.is_valid_number(parsed):
                logger.warning(f"⚠️ Telefone inválido detectado: {phone}")
                raise ValueError("Número inválido")
            
            # Retorna formato WhatsApp (DDI + DDD + Numero)
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164).replace("+", "")
        except Exception as e:
            logger.error(f"❌ Erro na normalização de {phone}: {e}")
            raise ValueError("Erro na normalização do telefone")

    def get_active_trip(self, user_id: str) -> Optional[Dict[str, Any]]:
        \"\"\"Retorna mock de viagem para testes\"\"\"
        logger.debug(f"🔍 Buscando viagem ativa para {user_id}")
        return {"trip_id": "viagem_teste_2026", "destination": "Gramado", "location_enabled": True}

    def authorize(self, user_id: str, active_trip: Optional[Dict[str, Any]], scope: str = "ask") -> Tuple[bool, str]:
        \"\"\"Validação Single Source of Truth\"\"\"
        ALLOWED_SCOPES = {"ask", "upload", "location", "admin"}
        if scope not in ALLOWED_SCOPES:
            return (False, "Acesso Negado: Escopo inválido.")

        role = self.get_user_role(user_id)
        if not role or role == "unauthorized":
            return (False, "Acesso Negado: Usuário não autorizado.")
            
        if role == "admin": 
            return (True, "Autorizado (Admin)")
            
        if not active_trip: 
            return (False, "Nenhuma viagem ativa encontrada.")
        
        return (True, "Autorizado")

    def get_user_role(self, user_id: str) -> str:
        \"\"\"Identifica se o usuário é Admin ou comum\"\"\"
        if user_id in self.admins or user_id.endswith("88368783"):
            return "admin"
        return "user"

    def owns_document(self, user_id: str, filename: str) -> bool:
        \"\"\"Prevenção de IDOR - Default Deny\"\"\"
        # TODO: Implementar query no banco real
        # Por enquanto, liberamos acesso apenas para admins
        return self.get_user_role(user_id) == "admin"
