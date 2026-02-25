from langchain_chroma import Chroma
from langchain_core.documents import Document
import os

class MockEmbeddings:
    def embed_documents(self, texts):
        return [[0.1] * 1536 for _ in texts]
    def embed_query(self, text):
        return [0.1] * 1536

def test_chroma_mock():
    print("[*] Testando Chroma com MockEmbeddings...")
    persist_dir = "./data/chroma_mock"
    if not os.path.exists(persist_dir):
        os.makedirs(persist_dir)
        
    try:
        embeddings = MockEmbeddings()
        vector_store = Chroma(
            collection_name="mock_collection",
            embedding_function=embeddings,
            persist_directory=persist_dir
        )
        
        doc = Document(page_content="Teste 123", metadata={"id": 1})
        print("[*] Chamando add_documents...")
        vector_store.add_documents([doc])
        print("✅ Sucesso ao adicionar!")
        
        print("[*] Chamando similarity_search...")
        res = vector_store.similarity_search("Teste", k=1)
        print(f"✅ Sucesso ao buscar! Resultado: {res[0].page_content}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    test_chroma_mock()
