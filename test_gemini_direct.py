import requests

def test_new_gemini():
    # A sua chave oficial do AI Studio
    api_key = "AIzaSyA-Dn8iSHHyYctor9DT_zpjk3u5AmcM7wo"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": "Diga apenas 'Conectado com sucesso!' e nada mais."}]}]
    }
    
    print("\n--- ✨ TESTE DIRETO: GEMINI 2.0 FLASH ---")
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if r.status_code == 200:
            resposta = r.json()['candidates'][0]['content']['parts'][0]['text']
            print(f"✅ SUCESSO! O Gemini respondeu: {resposta}")
        elif r.status_code == 429:
            print("❌ ERRO 429: Cota esgotada ou zerada.")
            print("Detalhes: O Google exige que você clique em 'Configurar Faturamento' para liberar a cota gratuita.")
        else:
            print(f"⚠️ Status inesperado: {r.status_code}")
            print(r.text)
            
    except Exception as e:
        print(f"🚨 Erro de conexão: {e}")

if __name__ == "__main__":
    test_new_gemini()
