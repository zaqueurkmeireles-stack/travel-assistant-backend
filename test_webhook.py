import requests
import json

def test_webhook():
    url = "http://localhost:8000/webhook/whatsapp/text"
    
    # Payload simulando o que vem do n8n/Evolution API
    payload = {
        "key": {
            "remoteJid": "5511999999999@s.whatsapp.net",
            "fromMe": False,
            "id": "ABC123XYZ"
        },
        "message": {
            "conversation": "Olá! Gostaria de planejar uma viagem para a Chapada dos Veadeiros."
        },
        "pushName": "Teste Usuário"
    }
    
    print(f"[*] Enviando payload para {url}...")
    try:
        response = requests.post(url, json=payload)
        print(f"[OK] Status Code: {response.status_code}")
        print(f"[DATA] Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"[ERROR] Erro ao testar: {e}")

if __name__ == "__main__":
    test_webhook()
