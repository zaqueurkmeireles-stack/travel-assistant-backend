import requests
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_booking_api(api_key):
    # Endpoint comum do Booking.com na RapidAPI (API-DOJO)
    url = "https://booking-com.p.rapidapi.com/v1/metadata/exchange-rates"
    
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
    }

    print(f"Testando a chave: {api_key[:10]}... na RapidAPI (Booking.com)")
    
    try:
        # Usando locale 'pt-br' para teste básico
        response = requests.get(url, headers=headers, params={"currency": "AED", "locale": "pt-br"})
        
        if response.status_code == 200:
            print("\n✅ SUCESSO! A chave da API é VÁLIDA e está funcionando para o Booking.com na RapidAPI.")
            print("Resposta da API (Amostra):", str(response.json())[:100] + "...")
        elif response.status_code == 403:
            print("\n❌ ERRO 403: A chave da API é INVÁLIDA, expirada ou você não está inscrito nesta API específica na RapidAPI.")
            print("Detalhes:", response.text)
        elif response.status_code == 401:
            print("\n❌ ERRO 401: Não autorizado. Verifique se copiou a chave corretamente.")
            print("Detalhes:", response.text)
        elif response.status_code == 429:
            print("\n⚠️ ERRO 429: Limite de requisições excedido para esta chave.")
        else:
            print(f"\n⚠️ Código de status retornado: {response.status_code}")
            print("Corpo da resposta:", response.text)

    except Exception as e:
        print(f"\n❌ Erro ao tentar conectar com a API: {e}")

if __name__ == "__main__":
    key = "cb44b2d1acmsha7db96ec5484957p11b134jsn13348b425ba0"
    test_booking_api(key)
