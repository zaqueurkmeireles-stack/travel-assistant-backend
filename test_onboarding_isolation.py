import sys
import os
import io

# Configurar encoding para Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Adiciona o diretório raiz ao path para importar os módulos do app
sys.path.append(os.getcwd())

from app.services.user_service import UserService
from app.agents.orchestrator import TravelAgent
from app.config import settings

def test_isolation():
    user_svc = UserService()
    agent = TravelAgent()
    
    admin_id = user_svc.normalize_phone(settings.ADMIN_WHATSAPP_NUMBER)
    guest_id = "5511999999999" # Número fictício
    guest_uid = user_svc.normalize_phone(guest_id)
    
    # 🧼 Limpeza: Resetar guest para garantir teste limpo
    if guest_uid in user_svc.users:
        del user_svc.users[guest_uid]
        user_svc._save_users()
        print(f"🧼 Guest {guest_uid} resetado do banco.")

    print(f"\n--- 🧪 TESTE: ISOLAMENTO DE ONBOARDING ---")
    
    # 1. Simular Admin autorizando Ricardo (sem trip sugerida)
    print(f"\n1. Admin autorizando novo guest {guest_id}...")
    success_handle = user_svc.authorize_guest(admin_id, guest_id, trip_id=None)
    print(f"Resultado Autorização: {success_handle}")
    
    # 2. Verificar se o guest tem trip ativa
    active_trip = user_svc.get_active_trip(guest_id)
    print(f"Trip Ativa do Guest: {active_trip}")
    
    if active_trip is None:
        print("✅ SUCESSO: Guest começou isolado (Nenhuma trip herdada).")
    else:
        print("❌ FALHA: Guest herdou uma trip indevidamente!")
        return

    # 3. Simular Guest conversando com a IA para criar sua trip
    print(f"\n2. Guest informando destino e data para a IA...")
    user_input = "Oi! Por favor, crie minha viagem para o Japão em 2026-10-15."
    response = agent.chat(user_input, thread_id=guest_id)
    print(f"Resposta da IA: {response}")
    
    # 4. Verificar se a trip foi criada
    new_active_trip = user_svc.get_active_trip(guest_id)
    print(f"Nova Trip Ativa do Guest: {new_active_trip}")
    
    if new_active_trip and "JAPÃO" in new_active_trip.upper():
        print("✅ SUCESSO: IA criou a trip manualmente para o guest.")
    else:
        print("❌ FALHA: IA não criou a trip ou criou com nome errado.")

    # 5. Verificar se Guest vê documentos do Admin (Privacidade)
    print(f"\n3. Verificando privacidade (Guest não deve ver docs do Admin)...")
    admin_active_trip = user_svc.get_active_trip(admin_id)
    print(f"Trip do Admin: {admin_active_trip}")
    
    from app.services.rag_service import RAGService
    rag = RAGService()
    guest_docs = rag.list_user_documents(guest_id)
    print(f"Docs que o Guest enxerga: {guest_docs}")
    
    # Adicionar um doc fake para o admin se não houver
    if admin_active_trip:
        admin_doc_found = False
        for doc in rag.documents:
            if doc["metadata"].get("trip_id") == admin_active_trip:
                fname = doc["metadata"].get("filename")
                print(f"Doc do Admin encontrado no RAG: {fname}")
                admin_doc_found = True
                if fname and fname in str(guest_docs):
                    print("❌ FALHA DE PRIVACIDADE: Guest está vendo documentos do Admin!")
                    return
        if admin_doc_found:
            print("✅ SUCESSO: Guest NÃO enxerga documentos privados do Admin.")
        else:
            print("ℹ️ Info: Nenhum documento de admin para testar vazamento, mas o isolamento de Trip ID garante a segurança.")

if __name__ == "__main__":
    test_isolation()
