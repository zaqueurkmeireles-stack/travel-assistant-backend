import requests
import sys
import os
import json
import io

# Configuração para evitar erro de Unicode no Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuração de Cores para Terminal
class Colors:
    OK = '\033[92m'
    INFO = '\033[94m'
    WARN = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

BASE_URL = "http://localhost:80" # Porta padrão no Easypanel/Docker que configuramos

def print_test(name, result, detail=""):
    status = f"{Colors.OK}✅ SUCESSO" if result else f"{Colors.FAIL}❌ FALHA"
    print(f"{Colors.BOLD}[ {name} ]{Colors.END} {status} {Colors.END}")
    if detail:
        print(f"   └─ {detail}")

def test_health():
    try:
        r = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print_test("Health Check", r.status_code == 200, f"Status: {r.status_code} - {r.json().get('service')}")
    except Exception as e:
        print_test("Health Check", False, str(e))

def test_chat():
    payload = {
        "user_id": "test_cmd_user_999",
        "message": "Olá, quem é você e para onde vamos?"
    }
    try:
        r = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=10)
        # O chat responde 200 após processar (ou 202 se for bypass)
        print_test("Chat API", r.status_code in [200, 202], f"Resposta recebida de {payload['user_id']}")
    except Exception as e:
        print_test("Chat API", False, str(e))

def test_manifest():
    try:
        r = requests.get(f"{BASE_URL}/manifest.json", timeout=5)
        is_pwa = r.status_code == 200 and "Seven" in r.text
        print_test("PWA Manifest", is_pwa, "Arquivo manifest.json acessível e válido")
    except Exception as e:
        print_test("PWA Manifest", False, str(e))

def test_upload_sample():
    # Cria um arquivo de texto fake para teste se não houver um PDF
    sample_file = "test_sample_doc.txt"
    with open(sample_file, "w") as f:
        f.write("Reserva de Hotel: Hilton Paris. Data: 2024-12-25. Código: HLT123")
    
    try:
        with open(sample_file, "rb") as f:
            files = {"file": (sample_file, f, "text/plain")}
            data = {"document_hint": "Teste via CMD"}
            r = requests.post(f"{BASE_URL}/api/upload-document", files=files, data=data, timeout=15)
            
        success = r.status_code == 200 and r.json().get("success") != False
        detail = f"Tipo detectado: {r.json().get('document_type', 'N/A')}" if success else r.text
        print_test("Upload Document", success, detail)
    except Exception as e:
        print_test("Upload Document", False, str(e))
    finally:
        if os.path.exists(sample_file):
            os.remove(sample_file)

if __name__ == "__main__":
    print(f"\n{Colors.BOLD}{Colors.INFO}🧪 INICIANDO TESTES DO SEVEN ASSISTANT (CMD MODE){Colors.END}\n")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--active":
        # Se o usuário quiser testar com o servidor rodando em outra janela
        test_health()
        test_chat()
        test_manifest()
        test_upload_sample()
    else:
        print(f"{Colors.WARN}💡 Dica: Certifique-se que o servidor está rodando em outra aba (python main.py){Colors.END}")
        print(f"Executando testes básicos...\n")
        test_health()
        test_manifest()
        print(f"\nPara testes completos (Chat/Upload), execute: {Colors.BOLD}python test_vault.py --active{Colors.END}")

    print(f"\n{Colors.INFO}--- Fim dos Testes ---{Colors.END}\n")
