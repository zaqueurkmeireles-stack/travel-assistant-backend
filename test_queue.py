from app.services.user_service import UserService
from app.services.rag_service import RAGService
import json

def test_batch_queue():
    user_svc = UserService()
    user_svc.db_path = "data/test_users_db.json" # Isolated test
    user_svc.users = {}
    
    user_id = "5511999999999"
    norm_id = user_svc.normalize_phone(user_id)
    user_svc.users[norm_id] = {"role": "admin", "authorized_trips": ["trip_1"], "active_trip_id": "trip_1"}
    
    print(f"Testing with normalized ID: {norm_id}")
    
    print("\n--- TESTE 1: Pushing 3 documents to the queue ---")
    docs = [
        {"filename": "passagem1.pdf", "document_type": "passagem", "traveler": "Joao"},
        {"filename": "passagem2.pdf", "document_type": "passagem", "traveler": "Maria"},
        {"filename": "hotel.pdf", "document_type": "hotel", "traveler": "Joao"}
    ]
    
    for doc in docs:
        user_svc.set_pending_substitution(user_id, doc)
        print(f"Pushed: {doc['filename']}")
        
    count = user_svc.get_pending_substitutions_count(user_id)
    print(f"Queue size: {count}")
    assert count == 3, f"Expected 3, got {count}"
    
    print("\n--- TESTE 2: Popping items ---")
    item1 = user_svc.get_pending_substitution(user_id)
    print(f"First item: {item1['filename']}")
    assert item1['filename'] == "passagem1.pdf"
    
    user_svc.clear_pending_substitution(user_id)
    print("Cleared first item")
    
    count2 = user_svc.get_pending_substitutions_count(user_id)
    print(f"Queue size: {count2}")
    assert count2 == 2, f"Expected 2, got {count2}"
    
    item2 = user_svc.get_pending_substitution(user_id)
    print(f"Second item: {item2['filename']}")
    assert item2['filename'] == "passagem2.pdf"
    
    print("\n✅ TESTE DE FILA CONCLUÍDO COM SUCESSO!")

if __name__ == "__main__":
    test_batch_queue()
