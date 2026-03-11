from loguru import logger
import os

class UserService:
    def __init__(self):
        self.admin_phones = os.getenv("ADMIN_PHONES", "").split(",")

    def normalize_phone(self, phone: str) -> str:
        return "".join(filter(str.isdigit, phone))

    def get_active_trip(self, user_id: str):
        # Por enquanto retorna um ID fixo para teste, 
        # mas aqui buscaremos no Supabase em breve.
        return "trip_teste_001"

    def authorize(self, user_id: str, trip_id: str, scope: str = "ask"):
        if user_id in self.admin_phones:
            return True, "admin"
        return True, "member"
