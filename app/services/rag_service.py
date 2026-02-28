"""
RAG Service - Gerenciamento de Memória Vetorial Robusto (NumPy Puro + JSON)
Substitui o ChromaDB e evita dependências pesadas como scikit-learn ou ONNX.
"""

import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
from langchain_openai import OpenAIEmbeddings
from app.config import settings
from loguru import logger

class RAGService:
    """Service para busca semântica robusta usando Embeddings da OpenAI e NumPy Puro"""
    
    def __init__(self):
        """Inicializa a base de dados local"""
        self.data_path = os.path.join(settings.CHROMA_DB_PATH, "vector_data.json")
        self.embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
        self.documents = []
        self.vectors = []
        
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        
        # Carregar dados existentes
        self._load_data()
        logger.info(f"✅ RAG Service NumPy inicializado (Base em: {self.data_path})")
        
    def _load_data(self):
        """Carrega os documentos e vetores do disco"""
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    self.documents = content.get("documents", [])
                    raw_vectors = content.get("vectors", [])
                    if raw_vectors:
                        self.vectors = np.array(raw_vectors)
                logger.info(f"📂 {len(self.documents)} documentos carregados da memória.")
            except Exception as e:
                logger.error(f"❌ Erro ao carregar dados do RAG: {e}")
                
    def _save_data(self):
        """Salva os documentos e vetores no disco"""
        try:
            content = {
                "documents": self.documents,
                "vectors": self.vectors.tolist() if len(self.vectors) > 0 else []
            }
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ Erro ao salvar dados do RAG: {e}")

    def delete_documents_by_type(self, thread_id: str, document_type: str, trip_id: str = None) -> int:
        """Remove documentos do mesmo tipo para evitar duplicatas ao atualizar informações."""
        try:
            self._load_data()  # garantir dados frescos do disco
            if not self.documents:
                return 0
            indices_to_remove = []
            for i, doc in enumerate(self.documents):
                m = doc["metadata"]
                same_user = m.get("thread_id") == thread_id
                same_type = m.get("document_type", "").lower() == document_type.lower()
                same_trip = (trip_id and m.get("trip_id") == trip_id) or (not trip_id)
                if same_user and same_type and same_trip:
                    indices_to_remove.append(i)
            if not indices_to_remove:
                return 0
            for i in sorted(indices_to_remove, reverse=True):
                self.documents.pop(i)
                if len(self.vectors) > 1:
                    self.vectors = np.delete(self.vectors, i, axis=0)
                else:
                    self.vectors = np.array([])
            self._save_data()
            logger.info(f"🗑️ {len(indices_to_remove)} doc(s) antigo(s) tipo '{document_type}' removidos para {thread_id}")
            return len(indices_to_remove)
        except Exception as e:
            logger.error(f"❌ Erro ao remover docs antigos: {e}")
            return 0

    def delete_data_by_trip(self, trip_id: str) -> int:
        """Remove TODOS os documentos vinculados a uma viagem específica (Cleanup)."""
        try:
            self._load_data()
            if not self.documents:
                return 0
            
            indices_to_remove = [
                i for i, doc in enumerate(self.documents) 
                if doc["metadata"].get("trip_id") == trip_id
            ]
            
            if not indices_to_remove:
                return 0
                
            for i in sorted(indices_to_remove, reverse=True):
                self.documents.pop(i)
                if len(self.vectors) > 1:
                    self.vectors = np.delete(self.vectors, i, axis=0)
                else:
                    self.vectors = np.array([])
            
            self._save_data()
            logger.info(f"🧹 Cleanup: {len(indices_to_remove)} documentos removidos da trip {trip_id}")
            return len(indices_to_remove)
        except Exception as e:
            logger.error(f"❌ Erro no cleanup da trip {trip_id}: {e}")
            return 0


    def add_document(self, text: str, metadata: Dict[str, Any]):
        """Gera embedding e adiciona o documento à base"""
        try:
            logger.info(f"📥 Indexando novo documento: {metadata.get('filename')}")
            
            # Gerar embedding via OpenAI
            vector = self.embeddings.embed_query(text)
            
            # Adicionar ao estado em memória
            self.documents.append({
                "text": text,
                "metadata": metadata
            })
            
            if len(self.vectors) == 0:
                self.vectors = np.array([vector])
            else:
                self.vectors = np.vstack([self.vectors, vector])
                
            # Persistir
            self._save_data()
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar documento: {e}")
            return False
            
    def _cosine_similarity(self, v1: np.ndarray, v2_matrix: np.ndarray) -> np.ndarray:
        """Calcula a similaridade de cosseno manual usando NumPy"""
        # v1 shape: (1, dim), v2_matrix shape: (N, dim)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2_matrix, axis=1)
        
        dot_product = np.dot(v2_matrix, v1.T).flatten()
        return dot_product / (norm_v1 * norm_v2)

    def query(self, query_text: str, thread_id: str, k: int = 3) -> str:
        """Busca semântica filtrada por viagem ativa do usuário"""
        if not self.documents:
            return "Você ainda não enviou nenhum documento de viagem."
            
        try:
            logger.info(f"🔍 Buscando no RAG: '{query_text}' (Usuario: {thread_id})")
            
            from app.services.user_service import UserService
            user_service = UserService()
            active_trip = user_service.get_active_trip(thread_id)
            
            # Gerar embedding da query
            query_vector = np.array(self.embeddings.embed_query(query_text))
            
            # Filtrar documentos pelo trip_id (ou fallback para o próprio thread_id)
            user_indices = []
            for i, doc in enumerate(self.documents):
                m_trip = doc["metadata"].get("trip_id")
                m_thread = doc["metadata"].get("thread_id")
                if (active_trip and m_trip == active_trip) or m_thread == thread_id:
                    user_indices.append(i)
            
            if not user_indices:
                return "Nenhuma informação relevante encontrada nos documentos enviados."
                
            # Pegar os vetores filtrados
            user_vectors = self.vectors[user_indices]
            
            # Calcular similaridades
            similarities = self._cosine_similarity(query_vector, user_vectors)
            
            # Pegar os top K resultados
            top_indices_local = np.argsort(similarities)[::-1][:k]
            top_indices_global = [user_indices[i] for i in top_indices_local]
            
            results = []
            for idx in top_indices_global:
                results.append(self.documents[idx]["text"])
                
            return "\n---\n".join(results)
            
        except Exception as e:
            logger.error(f"❌ Erro na consulta ao RAG: {e}")
            return f"Erro ao acessar documentos: {str(e)}"

    def list_user_documents(self, thread_id: str) -> List[str]:
        """Lista nomes de arquivos enviados para a viagem atual do usuário ou para o próprio usuário"""
        from app.services.user_service import UserService
        user_service = UserService()
        active_trip = user_service.get_active_trip(thread_id)
        
        filenames = set()
        for doc in self.documents:
            m_trip = doc["metadata"].get("trip_id")
            m_thread = doc["metadata"].get("thread_id")
            if (active_trip and m_trip == active_trip) or m_thread == thread_id:
                if doc["metadata"].get("filename"):
                    filenames.add(doc["metadata"]["filename"])
                    
        return list(filenames)
