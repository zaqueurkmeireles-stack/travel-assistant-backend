import os
from dotenv import load_dotenv
from supabase import create_client

# Carrega as chaves do seu .env
load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("❌ Erro: Chaves do Supabase não encontradas no .env")
    exit()

supabase = create_client(url, key)

# Seus dados para o cadastro inicial
user_data = {
    "name": "Zaqueu Master",
    "phone": "5541988368783",
    "api_key": "antigravity_dev_key"
}

try:
    # Tenta inserir na tabela 'users'
    res = supabase.table("users").insert(user_data).execute()
    print("✅ USUÁRIO CRIADO COM SUCESSO NO SUPABASE!")
    print(f"ID Gerado: {res.data[0]['id']}")
except Exception as e:
    print(f"⚠️ Aviso: O usuário já deve existir ou houve um erro: {e}")
