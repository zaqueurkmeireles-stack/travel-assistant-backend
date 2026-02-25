import google.generativeai as genai
from app.config import settings
import os

def list_gemini_models():
    api_key = settings.GOOGLE_GEMINI_API_KEY
    if not api_key:
        print("[-] API Key não encontrada no config.")
        return

    print(f"[*] Verificando modelos disponíveis para a chave: {api_key[:10]}...")
    
    genai.configure(api_key=api_key)
    
    try:
        models = genai.list_models()
        print("\n[MODELOS DISPONÍVEIS]")
        count = 0
        for m in models:
            print(f"- {m.name} (Suporta: {', '.join(m.supported_generation_methods)})")
            count += 1
        
        if count == 0:
            print("[-] Nenhum modelo retornado. A chave pode estar restrita ou a API desativada.")
            
    except Exception as e:
        print(f"[ERROR] Erro ao listar modelos: {e}")

if __name__ == "__main__":
    list_gemini_models()
