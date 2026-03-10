import os
import re
from loguru import logger

def verify_sync():
    logger.info("🔍 Iniciando Verificação de Sincronia Antigravity...")
    
    # 1. Checar Requirements (Forçando UTF-8)
    if os.path.exists("requirements.txt"):
        with open("requirements.txt", "r", encoding="utf-8") as f:
            content = f.read().lower()
            if "phonenumbers" in content:
                print("✅ [OK] requirements.txt atualizado com phonenumbers.")
            else:
                print("❌ [ERRO] phonenumbers NÃO encontrado no arquivo!")
    
    # 2. Checar Versão da Rota (Forçando UTF-8)
    route_path = "app/api/routes.py"
    if os.path.exists(route_path):
        with open(route_path, "r", encoding="utf-8") as f:
            head = f.read(1000)
            version = re.search(r"Versão: (.*)", head)
            if version:
                print(f"✅ [OK] Routes.py na versão: {version.group(1)}")
            else:
                print("⚠️ [AVISO] Versão não detectada no cabeçalho.")

    # 3. Checar UserService (Forçando UTF-8)
    service_path = "app/services/user_service.py"
    if os.path.exists(service_path):
        with open(service_path, "r", encoding="utf-8") as f:
            content = f.read()
            if "phonenumbers" in content:
                print("✅ [OK] UserService está com a lógica blindada.")
            else:
                print("❌ [ERRO] UserService parece estar desatualizado!")

if __name__ == "__main__":
    try:
        verify_sync()
    except Exception as e:
        print(f"❌ Erro ao rodar verificação: {e}")
