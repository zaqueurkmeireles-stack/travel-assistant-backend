
import requests
import json

URL = "http://localhost:8000/api/webhook/location"

payload = {
    "user_id": "5541988368783",
    "latitude": 38.7813,
    "longitude": -9.1359,
    "address": "Gate 15, Aeroporto de Lisboa (LIS)"
}

print(f"Simulando chegada no Portão 15 de Lisboa: {payload['latitude']}, {payload['longitude']}")
try:
    response = requests.post(URL, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"Erro: {e}")
