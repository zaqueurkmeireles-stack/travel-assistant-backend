import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_n8n_connectivity():
    url = os.getenv("N8N_WEBHOOK_URL_OUTPUT")
    print(f"Testing connectivity to: {url}")
    
    payload = {
        "telefone": "5511999999999",
        "mensagem": "Teste de conectividade do TravelCompanion AI",
        "origem": "backend_test"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("SUCCESS: Backend can reach n8n!")
        else:
            print("WARNING: Reached n8n but received an error.")
            
    except Exception as e:
        print(f"FAILED: Could not reach n8n. Error: {e}")

if __name__ == "__main__":
    test_n8n_connectivity()
