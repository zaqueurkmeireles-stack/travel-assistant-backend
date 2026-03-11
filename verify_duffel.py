import requests

def check_duffel_live():
    api_key = "duffel_live_ztJJ7GI7YYnDt2Ki9O3-a-IboaAg2c_hVqVH3qxbR5s"
    url = "https://api.duffel.com/air/airlines?limit=1"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Duffel-Version": "v2",  # A versão oficial e definitiva
        "Content-Type": "application/json"
    }
    
    print("--- ✈️ DUFFEL LIVE AUDIT (V4 - O Veredito) ---")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ CHAVE VÁLIDA: Conexão v2 estabelecida com sucesso!")
            print(f"📡 Dados da Companhia: {response.json()['data'][0]['name']}")
        else:
            print(f"❌ STATUS {response.status_code}")
            print(f"Mensagem: {response.text}")
            
    except Exception as e:
        print(f"🚨 Erro de Conexão: {str(e)}")

if __name__ == "__main__":
    check_duffel_live()
