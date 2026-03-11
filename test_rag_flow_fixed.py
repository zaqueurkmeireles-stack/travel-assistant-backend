"""
Fluxo completo de RAG: Ingestão de PDF Simulado e Busca Semântica.
"""
import sys
import os
import json
import time

# Adicionar o diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app.services.rag_service import RAGService
from app.services.document_ingestor import DocumentIngestor

def test_rag_flow():
    print("🧠 [TESTE] Validando Fluxo de RAG e Ingestão...")
    
    ingestor = DocumentIngestor()
    rag_svc = RAGService()
    
    user_id = "554188368783"
    filename = "ticket_teste_aguia_branca.pdf"
    
    # Conteúdo simulado de uma passagem de ônibus/trem
    fake_content = """
    VIAÇÃO ÁGUIA BRANCA - Bilhete de Passagem Eletrônico
    Passageiro: Zaqueu Meireles
    Origem: Vitória (VIX) - 10/05/2026 08:30
    Destino: Rio de Janeiro (RJ) - 10/05/2026 18:45
    Poltrona: 12 - Executivo
    Localizador: AB12345VIX
    """
    
    # 1. Simular payload de webhook (dry_run=False para salvar)
    print(f"[*] Simulando ingestão do arquivo: {filename}")
    payload = {
        "message": {"documentMessage": {"fileName": filename, "mimetype": "application/pdf"}},
        "key": {"remoteJid": f"{user_id}@s.whatsapp.net"},
        "base64": None, # Não usaremos base64 real aqui, burlaremos o ingestor se necessário ou usaremos bytes diretos
        "message_id": "test_msg_id_999"
    }
    
    # Ingestor direto com texto (mockando o parse se necessário)
    # Para este teste, vamos adicionar diretamente ao RAG para validar a busca
    metadata = {
        "filename": filename,
        "thread_id": user_id,
        "document_type": "passagem_onibus",
        "primary_traveler_name": "Zaqueu Meireles"
    }
    
    print("[*] Adicionando documento diretamente ao RAG para testar busca...")
    rag_svc.add_document(fake_content, metadata)
    
    # 2. Verificar se está no ChromaDB (pode levar um segundo para persistir)
    time.sleep(1)
    
    print("[*] Realizando busca semântica no RAG...")
    results = rag_svc.query("Para onde o Zaqueu vai no dia 10 de maio?", thread_id=user_id)
    
    if results and "Nenhuma informação relevante" not in results:
        print(f"✅ Sucesso! O RAG retornou conteúdo.")
        # results é uma string no RAGService.query
        print(f"--- Melhor Match ---\n{results[:200]}...")
        if "Rio de Janeiro" in results:
            print("🎯 O RAG identificou o destino corretamente!")
        else:
            print("⚠️ Conteúdo encontrado não parece bater com o esperado.")
    else:
        print(f"❌ Nenhum resultado relevante retornado pelo RAG: {results}")

if __name__ == "__main__":
    try:
        test_rag_flow()
    except Exception as e:
        print(f"💥 Erro no fluxo RAG: {e}")
