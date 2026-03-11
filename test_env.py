import os
from dotenv import load_dotenv

# Tenta carregar o arquivo .env
if load_dotenv():
    print("✅ Arquivo .env encontrado e carregado!")
else:
    print("❌ Arquivo .env NÃO encontrado na pasta atual.")

# Lista de chaves para verificar
keys_to_check = [
    "SUPABASE_URL", 
    "SUPABASE_SERVICE_ROLE_KEY", 
    "OPENAI_API_KEY", 
    "JWT_SECRET_KEY"
]

print("\n--- Verificação de Chaves ---")
for key in keys_to_check:
    value = os.getenv(key)
    if value:
        # Mostra apenas os 5 primeiros caracteres por segurança
        print(f"🟢 {key}: Carregada (Inicia com: {value[:5]}...)")
    else:
        print(f"🔴 {key}: NÃO ENCONTRADA")
