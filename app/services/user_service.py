import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from app.config import settings
from loguru import logger

class UserService:
    """Gerencia níveis de acesso, perfis de usuários e viagens ativas."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized: return
        self.db_path = os.path.join(os.path.dirname(settings.CHROMA_DB_PATH), "users_db.json")
        self.users: Dict[str, Dict[str, Any]] = {}
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._load_users()
        self._ensure_admin()
        self._initialized = True
        logger.debug(f"✅ UserService inicializado (Base: {self.db_path})")

    def _load_users(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    raw_users = json.load(f)
                    # Normalizar chaves carregadas e re-salvar com as novas chaves
                    normalized = {}
                    for k, v in raw_users.items():
                        norm_k = self.normalize_phone(k)
                        normalized[norm_k] = v
                    self.users = normalized
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

    def normalize_phone(self, phone: str) -> str:
        """
        Normaliza o número removendo o 9º dígito (Brasil) e preservando domínios de grupo.
        """
        if not phone: return ""
        
        phone_str = str(phone).strip().lower()
        
        # 🛡️ SE FOR GRUPO (@g.us), preservamos o JID completo para evitar DMs a estranhos
        if "@g.us" in phone_str:
            return phone_str
            
        # Para contatos normais (@s.whatsapp.net ou apenas número), limpamos para dígitos
        p = "".join(filter(str.isdigit, phone_str))
        
        # 🛡️ ALERTA: Se o input tinha caracteres mas resultou em nada (ex: "undefined")
        if not p and phone_str:
            if phone_str != "desconhecido":
                logger.warning(f"⚠️ Normalização resultou em vazio para o input: '{phone_str}'")
            return ""

        # Lógica para Brasil: se começa com 55 e tem 13 dígitos, remove o 9 (o 5º dígito)
        if p.startswith("55") and len(p) == 13:
            return p[:4] + p[5:]
        
        return p

    def _ensure_admin(self):
        admin_number = self.normalize_phone(getattr(settings, "ADMIN_WHATSAPP_NUMBER", ""))
        if admin_number and admin_number not in self.users:
            self.users[admin_number] = {
                "role": "admin",
                "authorized_trips": [],
                "active_trip_id": None,
                "created_at": datetime.now().isoformat()
            }
            self._save_users()
            logger.info(f"👑 Admin configurado: {admin_number}")

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        uid = self.normalize_phone(user_id)
        admin_number = self.normalize_phone(getattr(settings, "ADMIN_WHATSAPP_NUMBER", ""))
        
        if uid == admin_number and uid not in self.users:
            self._ensure_admin()
            
        return self.users.get(uid)

    def get_user_role(self, user_id: str) -> str:
        """Retorna 'admin', 'guest' ou 'unauthorized' com expiração inteligente baseada em viagens."""
        user = self.get_user(user_id)
        uid = self.normalize_phone(user_id)
        admin_number = self.normalize_phone(getattr(settings, "ADMIN_WHATSAPP_NUMBER", ""))
        
        if uid == admin_number and admin_number:
            self._ensure_admin()
            return "admin"
            
        if not user:
            return "unauthorized"
            
        role = user.get("role", "unauthorized")
        
        # [SMART EXPIRATION] Se for guest, verificar se ainda tem viagens ativas
        if role == "guest":
            authorized_trips = user.get("authorized_trips", [])
            if not authorized_trips:
                # Se não tem trip vinculada, mas foi marcado como guest, mantemos por 24h como carência inicial
                # Ou revertemos se for muito antigo. Para simplificar, vamos checar trips.
                return "guest" 

            from app.services.trip_service import TripService
            trip_svc = TripService()
            
            has_active_trip = False
            for trip_id in authorized_trips:
                if trip_svc.is_trip_active(trip_id, grace_days=2):
                    has_active_trip = True
                    break
            
            if not has_active_trip:
                logger.info(f"⏳ Acesso expirado para guest {uid} (Trip concluída + 2 dias).")
                return "unauthorized"
                
        return role

    def get_active_trip(self, user_id: str) -> Optional[str]:
        user = self.get_user(user_id)
        if not user:
            return None
        return user.get("active_trip_id")

    def set_active_trip(self, user_id: str, trip_id: str):
        uid = self.normalize_phone(user_id)
        admin_number = self.normalize_phone(getattr(settings, "ADMIN_WHATSAPP_NUMBER", ""))
        
        if uid not in self.users:
            if uid == admin_number and admin_number:
                self._ensure_admin()
            else:
                return False
                
        if trip_id not in self.users[uid].get("authorized_trips", []):
            self.users[uid].setdefault("authorized_trips", []).append(trip_id)
            
        self.users[uid]["active_trip_id"] = trip_id
        self._save_users()
        return True

    def authorize_guest(self, admin_id: str, guest_id: str, trip_id: str) -> Optional[str]:
        """Um admin autoriza um convidado para uma viagem. Retorna o trip_id se sucesso."""
        if self.get_user_role(admin_id) != "admin":
            logger.warning(f"Usuário {admin_id} não é admin e tentou autorizar {guest_id}")
            return None
            
        uid = self.normalize_phone(guest_id)
        
        if uid not in self.users:
            self.users[uid] = {
                "role": "guest",
                "authorized_trips": [],
                "active_trip_id": None,
                "created_at": datetime.now().isoformat()
            }
            
        if trip_id not in self.users[uid]["authorized_trips"]:
            self.users[uid]["authorized_trips"].append(trip_id)
            
        if not self.users[uid]["active_trip_id"]:
            self.users[uid]["active_trip_id"] = trip_id
            
        # [NOVO] Vincular retroativamente documentos que o convidado enviou ANTES da autorização
        try:
            from app.services.rag_service import RAGService
            rag = RAGService()
            rag.assign_trip_to_user_documents(uid, trip_id)
        except Exception as e:
            logger.error(f"⚠️ Falha ao vincular documentos retroativos para {uid}: {e}")

        # Limpa da fila de espera do Admin
        admin_number = self.normalize_phone(getattr(settings, "ADMIN_WHATSAPP_NUMBER", ""))
        pending = self.users.get(admin_number, {}).get("pending_requests", {})
        if uid in pending:
            del pending[uid]
            self.users[admin_number]["pending_requests"] = pending
            
        self._save_users()
        logger.info(f"✅ Usuário {uid} autorizado para a viagem {trip_id} por {admin_id}")
        return trip_id

    def register_access_request(self, guest_id: str, push_name: str = "Desconhecido", suggested_trip_id: str = None) -> bool:
        """Registra uma tentativa de acesso não autorizada. Retorna True se o admin deve ser notificado agora (throttle)."""
        uid = self.normalize_phone(guest_id)
        admin_number = self.normalize_phone(getattr(settings, "ADMIN_WHATSAPP_NUMBER", ""))
        
        self._ensure_admin()
        
        if not admin_number or admin_number not in self.users:
            logger.warning(f"⚠️ Erro ao registrar request: admin_number inválido ou não encontrado no BD.")
            return False
            
        pending_requests = self.users[admin_number].setdefault("pending_requests", {})
        # [MODIFICADO] Armazena objeto com data, nome e trip sugerida
        request_data = pending_requests.get(uid)
        
        now = datetime.now()
        
        # Se for o primeiro request ou já se passaram mais de 10 minutos desde o último, avise o admin
        should_notify = False
        if not request_data:
            should_notify = True
        else:
            try:
                # Se for o formato antigo (string de data), ou novo (dict)
                last_iso = request_data["timestamp"] if isinstance(request_data, dict) else request_data
                last_time = datetime.fromisoformat(last_iso)
                if (now - last_time).total_seconds() > 600: # 10 minutos
                    should_notify = True
            except:
                should_notify = True
                
        # Atualiza a data e nome da última tentativa sempre
        pending_requests[uid] = {
            "timestamp": now.isoformat(),
            "push_name": push_name,
            "suggested_trip_id": suggested_trip_id or (request_data.get("suggested_trip_id") if isinstance(request_data, dict) else None)
        }
        self.users[admin_number]["pending_requests"] = pending_requests
        self._save_users()
        
        return should_notify

    def set_pending_trip_link(self, guest_id: str, host_user_id: str, trip_id: str, destination: str, start_date: str):
        """Salva uma proposta de vinculação de viagem aguardando confirmação do guest."""
        uid = self.normalize_phone(guest_id)
        if uid not in self.users:
            self.users[uid] = {
                "role": "guest",
                "authorized_trips": [],
                "active_trip_id": None,
                "created_at": datetime.now().isoformat()
            }
        self.users[uid]["pending_trip_link"] = {
            "host_user_id": self.normalize_phone(host_user_id),
            "trip_id": trip_id,
            "destination": destination,
            "start_date": start_date,
            "created_at": datetime.now().isoformat()
        }
        self._save_users()
        logger.info(f"⏳ Proposta de vinculação salva para {uid} → trip {trip_id}")

    def get_pending_trip_link(self, user_id: str) -> dict:
        """Retorna a proposta de vinculação pendente para o usuário, se houver."""
        uid = self.normalize_phone(user_id)
        return self.users.get(uid, {}).get("pending_trip_link")

    def clear_pending_trip_link(self, user_id: str):
        """Remove a proposta de vinculação após o usuário responder."""
        uid = self.normalize_phone(user_id)
        if uid in self.users and "pending_trip_link" in self.users[uid]:
            del self.users[uid]["pending_trip_link"]
            self._save_users()

    def find_user_by_name_or_phone(self, query: str) -> Optional[tuple[str, str]]:
        """
        Busca um usuário (admin) pelo nome ou número para ajudar na vinculação.
        Retorna (user_id, name) ou None.
        """
        if not query: return None
        q = query.lower().strip()
        
        # Primeiro tenta por número normalizado
        norm_q = self.normalize_phone(q)
        if norm_q in self.users:
            return (norm_q, self.users[norm_q].get("name", norm_q))
            
        # Depois tenta por nome (se houver o campo name no BD)
        for uid, data in self.users.items():
            name = data.get("name", "").lower()
            if q in name and name != "":
                return (uid, data.get("name"))
                
        # [Fallback Especial] Se o usuário digitar "Zaqueu" e ele for o admin configurado
        admin_number = self.normalize_phone(getattr(settings, "ADMIN_WHATSAPP_NUMBER", ""))
        if "zaqueu" in q or "admin" in q:
            return (admin_number, "Zaqueu")
            
        return None

    def set_user_phase(self, user_id: str, phase: Optional[str]):
        """Define em qual fase de interação/cadastro o usuário está."""
        uid = self.normalize_phone(user_id)
        if uid not in self.users:
            self.users[uid] = {
                "role": "unauthorized",
                "authorized_trips": [],
                "created_at": datetime.now().isoformat()
            }
        self.users[uid]["phase"] = phase
        self._save_users()

    def get_user_phase(self, user_id: str) -> Optional[str]:
        """Retorna a fase atual do usuário."""
        user = self.get_user(user_id)
        return user.get("phase") if user else None

