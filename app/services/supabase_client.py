import os
from typing import Any, Dict, Optional

class SupabaseClient:
    def __init__(self) -> None:
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.client = None
        
        if self.url and self.key:
            try:
                from supabase import create_client
                self.client = create_client(self.url, self.key)
                print("✅ Supabase conectado com sucesso.")
            except Exception as e:
                print(f"❌ Erro ao conectar no Supabase: {e}")
        else:
            print("⚠️ MODO OFFLINE: Chaves do Supabase não encontradas no .env.")
            print("👉 O sistema funcionará com dados simulados (Mock).")

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not self.client:
            # Retorna um usuário "fake" para teste
            return {"id": user_id, "name": "Viajante de Teste", "phone": "5541999999999"}
        try:
            resp = self.client.table("users").select("*").eq("id", user_id).single().execute()
            return resp.data
        except Exception: return None

    def get_user_by_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        if not self.client:
            if api_key == "antigravity_dev_key":
                return {"id": "dev_user_123", "name": "Zaqueu Dev"}
            return None
        try:
            resp = self.client.table("users").select("*").eq("api_key", api_key).single().execute()
            return resp.data
        except Exception: return None

    def get_trip_context(self, trip_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        if not self.client:
            # Retorna uma viagem "fake" para teste
            return {
                "trip": {"id": trip_id, "destination": "Marte"},
                "user_role": "owner",
                "user_permissions": ["read", "write", "admin"]
            }
        try:
            trip_resp = self.client.table("trips").select("*").eq("id", trip_id).single().execute()
            members_resp = self.client.table("trip_members").select("*").eq("trip_id", trip_id).execute()
            return {
                "trip": trip_resp.data,
                "user_role": "owner",
                "user_permissions": ["read", "write"]
            }
        except Exception: return None

supabase_client = SupabaseClient()
