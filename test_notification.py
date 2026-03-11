import requests
import json
import uuid
import time

# URL do seu backend no Easypanel
URL = "https://wsdfsdf-travel-assistant-backend.nkfiyw.easypanel.host/api/chat"

# Simula um número de telefone aleatório (novo visitante)
fake_number = f"55119{str(uuid.uuid4().int)[:8]}"

payload = {
    "user_id": fake_number,
    "message": "Oi! Quero testar a viagem pro Caribe!"
}

headers = {
    "Content-Type": "application/json"
}

print(f"Enviando simulacao de mensagem do numero: {fake_number}")
print(f"URL Alvo: {URL}")

try:
    response = requests.post(URL, json=payload, headers=headers)
    print(f"\nStatus Code: {response.status_code}")
    
    try:
        print("Resposta do Servidor:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        print("Texto puro retornado:")
        print(response.text)
        
    print("\nVerifique agora o seu WhatsApp de Administrador (554188368783)!")

except requests.exceptions.RequestException as e:
    print(f"\nErro ao conectar com o backend: {e}")
