import requests

def test_openai(key):
    url = "https://api.openai.com/v1/models"
    headers = {"Authorization": f"Bearer {key}"}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200: return "✅ VÁLIDA (Autenticada e com acesso!)"
        elif r.status_code == 401: return "❌ INVÁLIDA (Não reconhecida)"
        elif r.status_code in [429, 402]: return "⚠️ VÁLIDA (Mas sem saldo/cota)"
        return f"❓ Status {r.status_code}: {r.text[:50]}"
    except Exception as e: return f"🚨 Erro: {e}"

def test_claude(key):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    # Payload mínimo só para bater na porta
    data = {"model": "claude-3-haiku-20240307", "max_tokens": 1, "messages": [{"role": "user", "content": "Oi"}]}
    try:
        r = requests.post(url, headers=headers, json=data, timeout=5)
        if r.status_code == 200: return "✅ VÁLIDA (Autenticada e com acesso!)"
        elif r.status_code == 401: return "❌ INVÁLIDA (Não reconhecida)"
        elif r.status_code in [400, 402, 429]: 
            # Anthropic costuma dar 400 para erro de billing em contas novas
            error_type = r.json().get('error', {}).get('type', '')
            if 'credit' in r.text.lower() or 'billing' in r.text.lower():
                return f"⚠️ VÁLIDA (Mas sem saldo: {error_type})"
            return f"⚠️ VÁLIDA (Mas restrita: {error_type})"
        return f"❓ Status {r.status_code}: {r.text[:50]}"
    except Exception as e: return f"🚨 Erro: {e}"

def test_google_maps(key):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address=Curitiba&key={key}"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get("status") == "OK": return "✅ VÁLIDA (Google Maps funcionando!)"
        elif data.get("status") == "REQUEST_DENIED": return "❌ INVÁLIDA para Maps"
        return f"⚠️ VÁLIDA (Mas com erro de cota: {data.get('status')})"
    except Exception as e: return f"🚨 Erro: {e}"

def test_google_gemini(key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200: return "✅ VÁLIDA (Google Gemini funcionando!)"
        elif r.status_code == 400: return "❌ INVÁLIDA para Gemini"
        elif r.status_code == 403: return "❌ INVÁLIDA (Acesso proibido, provavelmente é só do Maps)"
        return f"❓ Status {r.status_code}"
    except Exception as e: return f"🚨 Erro: {e}"


print("\n" + "="*50)
print("🔍 AUDITORIA DE CHAVES DE IA (VALIDAÇÃO DE AUTENTICAÇÃO)")
print("="*50)

key_openai = "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"
key_claude = "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"
key_google = "AIzaSyAl-uUlCM-JDd398Qsa_tyhX-dVoOwB75o"

print(f"🤖 OpenAI (GPT-4o):   {test_openai(key_openai)}")
print(f"🧠 Claude (Anthropic): {test_claude(key_claude)}")
print(f"🗺️ Google (Maps):      {test_google_maps(key_google)}")
print(f"✨ Google (Gemini):    {test_google_gemini(key_google)}")
print("="*50 + "\n")

