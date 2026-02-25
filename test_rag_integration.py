from app.services.rag_service import RAGService
from app.agents.orchestrator import TravelAgent
from loguru import logger

def test_rag_flow():
    rag = RAGService()
    agent = TravelAgent()
    thread_id = "test_user_rag_123"
    
    # 1. Simular ingestão de documento
    sample_text = (
        "Reserva de Hotel em Frankfurt\n"
        "Hotel: Steigenberger Icon Frankfurter Hof\n"
        "Data: 13 a 16 de Abril de 2026\n"
        "Localizador: FRK-998877\n"
        "Endereço: Am Kaiserplatz, 60311 Frankfurt am Main, Alemanha\n"
        "Observação: O café da manhã está incluso no pacote familiar."
    )
    
    metadata = {
        "filename": "reserva_hotel_frankfurt.pdf",
        "thread_id": thread_id,
        "document_type": "hotel"
    }
    
    print("[*] Inserindo documento no RAG...")
    success = rag.add_document(sample_text, metadata)
    
    if success:
        print("[SUCCESS] Documento indexado com sucesso!")
    else:
        print("[FAILURE] Falha ao indexar documento.")
        return

    # 2. Testar consulta direta ao RAG
    print(f"[*] Testando consulta direta ao RAG para '{thread_id}'...")
    search_result = rag.query("Qual o nome do meu hotel em Frankfurt?", thread_id)
    print(f"NR Resultado RAG: {search_result[:100]}...")
    
    if "Steigenberger" in search_result:
        print("[SUCCESS] RAG retornou o conteúdo correto!")
    else:
        print("[WARNING] RAG não retornou o esperado.")

    # 3. Testar o Agente usando a Tool
    user_input = "Oi, você sabe qual é o nome do hotel que reservei em Frankfurt e se tem café da manhã?"
    print(f"\n[*] Perguntando ao Agente: '{user_input}'")
    
    response = agent.chat(user_input, thread_id=thread_id)
    print(f"\n[AGENT RESPONSE]\n{response}\n")
    
    if "Steigenberger" in response and "café da manhã" in response.lower():
        print("[SUCCESS] SUCESSO: O Agente usou a memória (RAG) para responder!")
    else:
        print("[WARNING] O Agente pode não ter usado a ferramenta de documentos corretamente.")

if __name__ == "__main__":
    test_rag_flow()
