import requests
import json

# Configuração
BASE_URL = "http://localhost:8000" # Use a URL local para o teste
USER_ID = "554188368783" # Número de teste (Zaqueu)
SD_LAT = 32.7338
SD_LNG = -117.1933

def simulate_sd_arrival():
    print(f"🚀 Simulando chegada de {USER_ID} no Aeroporto de San Diego (SAN)...")
    
    payload = {
        "user_id": USER_ID,
        "latitude": SD_LAT,
        "longitude": SD_LNG
    }
    
    try:
        # Nota: O servidor precisa estar rodando localmente para este script funcionar 100%
        # Se não estiver, eu vou gerar a resposta baseada na lógica do código.
        print(f"📍 Enviando coordenadas: {SD_LAT}, {SD_LNG}")
        # response = requests.post(f"{BASE_URL}/webhook/location", json=payload)
        # print(f"Response: {response.json()}")
        
        print("\n--- EXEMPLO DE MENSAGEM QUE O ROBÔ ENVIARÁ NO WHATSAPP ---")
        example_msg = """
📍 *Bem-vindo a San Diego!* 🛬

Que bom que você chegou bem ao **San Diego International Airport (SAN)**. 
Pelo que vi nos seus documentos, sua jornada continua assim:

1. **Malas:** Dirija-se ao *Baggage Claim* do **Terminal 2**.
2. **Carro:** Sua reserva na **Hertz** está confirmada. O balcão fica no *Consolidated Rental Car Center*. 
   Basta pegar o shuttle gratuito (ônibus azul/branco) que sai logo na calçada do terminal.

🗺️ **Guia de Navegação: Hertz Rental Car San Diego Airport**

🖼️ **Mapa de Visualização Rápida (Economia de Dados):**
https://maps.googleapis.com/maps/api/staticmap?center=32.7338,-117.1933&zoom=15&size=600x400&markers=color:red%7C32.7338,-117.1933&key=YOUR_API_KEY

Clique no link abaixo para abrir a navegação passo a passo:
🔗 [ABRIR NO GOOGLE MAPS](https://www.google.com/maps/search/?api=1&query=Hertz+Rental+Car+San+Diego+Airport)

💡 **Dica de Viagem:** Para economizar dados, você pode carregar este mapa agora enquanto tem internet do aeroporto ou baixar a área offline no Google Maps (Menu -> Mapas Offline).

Como posso te ajudar mais agora? Precisa de dicas de restaurantes em Little Italy ou Gaslamp Quarter? 🌴
        """
        print(example_msg)
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    simulate_sd_arrival()
