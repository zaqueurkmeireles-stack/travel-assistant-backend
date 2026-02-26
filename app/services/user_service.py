import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from app.config import settings
from loguru import logger

class UserService:
    """Gerencia níveis de acesso, perfis de usuários e viagens ativas."""

    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(settings.CHROMA_DB_PATH), "users_db.json")
        self.users: Dict[str, Dict[str, Any]] = {}
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._load_users()
        self._ensure_admin()
        logger.info(f"✅ UserService inicializado (Base: {self.db_path})")

    def _load_users(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar usuários: {e}")
                self.users = {}
        else:
            self.users = {}

    def _save_users(self):
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar usuários: {e}")

    def _ensure_admin(self):
        admin_number = settings.ADMIN_WHATSAPP_NUMBER
        if admin_number and admin_number not in self.users:
            # Remover sufixos padronizados se existirem, mas o ideal é tratar no uso
            admin_id = admin_number
            if "@s.whatsapp.net" in admin_id:
                admin_id = admin_id.replace("@s.whatsapp.net", "")
            
            self.users[admin_id] = {
                "role": "admin",
                "authorized_trips": [],
                "active_trip_id": None,
                "created_at": datetime.now().isoformat()
            }
            self._save_users()
            logger.info(f"👑 Admin configurado: {admin_id}")

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        # Remove sufixos do whatsapp por segurança
        uid = user_id.replace("@s.whatsapp.net", "")
        
        # Para evitar bloquear o administrador se ele não estiver no arquivo mas estiver na variável de ambiente
        if uid == settings.ADMIN_WHATSAPP_NUMBER and uid not in self.users:
            self._ensure_admin()
            
        return self.users.get(uid)

    def get_user_role(self, user_id: str) -> str:
        """Retorna 'admin', 'guest' ou 'unauthorized'"""
        user = self.get_user(user_id)
        if not user:
            # Fallback: se o USER_ID bater com o ADMIN da env local, cria ele como admin
            uid = user_id.replace("@s.whatsapp.net", "")
            if uid == settings.ADMIN_WHATSAPP_NUMBER:
                self._ensure_admin()
                return "admin"
            return "unauthorized"
        return user.get("role", "unauthorized")

    def get_active_trip(self, user_id: str) -> Optional[str]:
        user = self.get_user(user_id)
        if not user:
            return None
        return user.get("active_trip_id")

    def set_active_trip(self, user_id: str, trip_id: str):
        uid = user_id.replace("@s.whatsapp.net", "")
        # Adiciona aos usuários da trip se já existir no banco (para Admin principalmente)
        if uid not in self.users:
            if uid == settings.ADMIN_WHATSAPP_NUMBER:
                self._ensure_admin()
            else:
                return False
                
        if trip_id not in self.users[uid].get("authorized_trips", []):
            self.users[uid].setdefault("authorized_trips", []).append(trip_id)
            
        self.users[uid]["active_trip_id"] = trip_id
        self._save_users()
        return True

    def authorize_guest(self, admin_id: str, guest_id: str, trip_id: str) -> bool:
        """Um admin autoriza um convidado para uma viagem."""
        if self.get_user_role(admin_id) != "admin":
            logger.warning(f"Usuário {admin_id} não é admin e tentou autorizar {guest_id}")
            return False
            
        uid = guest_id.replace("@s.whatsapp.net", "")
        
        if uid not in self.users:
            self.users[uid] = {
                "role": "guest",
                "authorized_trips": [],
                "active_trip_id": None,
                "created_at": datetime.now().isoformat()
            }
            
        if trip_id not in self.users[uid]["authorized_trips"]:
            self.users[uid]["authorized_trips"].append(trip_id)
            
        # Define a viagem ativa para o guest, se ele não tiver nenhuma
        if not self.users[uid]["active_trip_id"]:
            self.users[uid]["active_trip_id"] = trip_id
            
        self._save_users()
        logger.info(f"✅ Usuário {uid} autorizado para a viagem {trip_id} por {admin_id}")
        return True
