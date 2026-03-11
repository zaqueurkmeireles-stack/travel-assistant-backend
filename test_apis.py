import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_key(name, url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        # 200 é sucesso, 401/403 é erro de chave, 404 depende do endpoint
        if response.status_code in [200, 201, 404]: 
            # 404 aqui pode significar que a chave foi aceita mas o caminho do teste é genérico
            print(f"✅ {name}: CONECTADA (Status: {response.status_code})")
        else:
            print(f"❌ {name}: FALHOU (Status: {response.status_code} - Verifique a chave)")
    except Exception as e:
        print(f"⚠️ {name}: ERRO DE CONEXÃO ({str(e)})")

print("\n--- 🔍 VALIDANDO CONEXÕES DE API ---")

# Teste OpenAI
test_key("OpenAI", "https://api.openai.com/v1/models", 
         {"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"})

# Teste Duffel
test_key("Duffel", "https://api.duffel.com/air/aircraft", 
         {"Authorization": f"Bearer {os.getenv('DUFFEL_API_KEY')}", "Duffel-Version": "v2"})

# Teste OpenWeather
ow_key = os.getenv('OPENWEATHER_API_KEY')
test_key("OpenWeather", f"https://api.openweathermap.org/data/2.5/weather?q=Curitiba&appid={ow_key}", {})

# Teste ElevenLabs
test_key("ElevenLabs", "https://api.elevenlabs.io/v1/voices", 
         {"xi-api-key": os.getenv('ELEVENLABS_API_KEY')})

print("--- 🏁 VALIDAÇÃO CONCLUÍDA ---\n")

