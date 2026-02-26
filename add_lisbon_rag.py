
from app.services.rag_service import RAGService

rag = RAGService()
rag.add_document(
    text="Voucher de Voo LH123: Partida Frankfurt (FRA) - Chegada Lisboa (LIS). Data: 2026-02-26. Passageiro: Zaqueu. Portão de desembarque: Terminal 1.",
    metadata={"type": "flight", "destination": "Lisbon", "user_id": "5541988368783", "thread_id": "5541988368783"}
)
print("✅ Documento de Lisboa adicionado ao RAG!")
