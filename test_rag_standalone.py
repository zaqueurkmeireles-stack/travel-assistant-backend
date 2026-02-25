from app.services.rag_service import RAGService
import os

def test_rag_standalone():
    print("[*] Testando RAGService Standalone...")
    try:
        print("[*] Inicializando RAGService...")
        rag = RAGService()
        print("[*] RAGService inicializado com sucesso.")
        thread_id = "standalone_test_user"
        text = "O código secreto da viagem é: 42-X-99"
        metadata = {"filename": "secret.txt", "thread_id": thread_id}
        
        print("[*] Adicionando documento...")
        rag.add_document(text, metadata)
        
        print("[*] Consultando...")
        result = rag.query("Qual o código secreto?", thread_id)
        print(f"[*] Resultado: {result}")
        
        if "42-X-99" in result:
            print("[SUCCESS] RAGService funcionando!")
        else:
            print("[FAILURE] Resultado nao contem o esperado.")
            
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rag_standalone()
