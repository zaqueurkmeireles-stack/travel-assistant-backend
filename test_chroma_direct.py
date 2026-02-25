import chromadb
from chromadb.config import Settings
import os

def test_chroma_direct():
    print("[*] Testando ChromaDB Direto (Sem LangChain)...")
    path = "./data/chroma_direct"
    if not os.path.exists(path):
        os.makedirs(path)
        
    try:
        client = chromadb.PersistentClient(path=path)
        print("[*] Cliente inicializado.")
        
        collection = client.get_or_create_collection(name="test_direct")
        print("[*] Coleção criada/obtida.")
        
        print("[*] Adicionando dado (sem embedding manual, usando padrão)...")
        # Nota: Por padrão ele usa SentenceTransformers se não passar nada, 
        # o que pode disparar o download.
        collection.add(
            documents=["O céu é azul", "A grama é verde"],
            ids=["id1", "id2"]
        )
        print("✅ Sucesso ao adicionar!")
        
        print("[*] Consultando...")
        results = collection.query(
            query_texts=["Qual a cor do céu?"],
            n_results=1
        )
        print(f"✅ Resultado: {results['documents']}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chroma_direct()
Line: 38
