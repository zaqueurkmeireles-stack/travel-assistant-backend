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
        """Carrega os documentos e vetores do disco com validação."""
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    
                    docs = content.get("documents", [])
                    raw_vectors = content.get("vectors", [])
                    
                    # Validação básica de integridade
                    if len(docs) != len(raw_vectors) and len(raw_vectors) > 0:
                        logger.error(f"⚠️ Inconsistência no RAG: {len(docs)} docs vs {len(raw_vectors)} vetores. Tentando recuperar...")
                        # Se houver inconsistência, limpamos os vetores para forçar re-indexação se necessário
                        # Ou apenas truncamos se possível. Aqui vamos manter os docs e avisar.
                        raw_vectors = raw_vectors[:len(docs)]
                    
                    self.documents = docs
                    if raw_vectors:
                        self.vectors = np.array(raw_vectors)
                    else:
                        self.vectors = np.array([])
                        
                logger.info(f"📂 {len(self.documents)} documentos carregados da memória.")
            except Exception as e:
                logger.error(f"❌ Erro crítico ao carregar dados do RAG: {e}")
                self.documents = []
                self.vectors = np.array([])
                
    def _save_data(self):
        """Salva os documentos e vetores no disco de forma ATÔMICA."""
        temp_path = self.data_path + ".tmp"
        try:
            content = {
                "documents": self.documents,
                "vectors": self.vectors.tolist() if len(self.vectors) > 0 else []
            }
            # 1. Escrever no arquivo temporário
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            
            # 2. Renomear para o original (Atômico no Unix/Windows overwrite)
            if os.path.exists(self.data_path):
                os.replace(temp_path, self.data_path)
            else:
                os.rename(temp_path, self.data_path)
                
        except Exception as e:
            logger.error(f"❌ Erro ao salvar dados do RAG de forma atômica: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def delete_documents_by_type(self, thread_id: str, document_type: str, trip_id: str = None, filename: str = None, traveler_name: str = None) -> int:
        """
        Remove documentos do mesmo tipo (e opcionalmente do mesmo nome/viajante) para evitar duplicatas.
        """
        try:
            self._load_data()
            if not self.documents:
                return 0
            indices_to_remove = []
            for i, doc in enumerate(self.documents):
                m = doc["metadata"]
                
                # Filtros Básicos
                if m.get("thread_id") != thread_id:
                    continue
                if m.get("document_type", "").lower() != document_type.lower():
                    continue
                if trip_id and m.get("trip_id") != trip_id:
                    continue
                    
                # Filtros Opcionais de Precisão
                if filename and m.get("filename") != filename:
                    continue
                if traveler_name and m.get("primary_traveler_name") != traveler_name:
                    continue
                
                indices_to_remove.append(i)
            
            if not indices_to_remove:
                return 0
            
            for i in sorted(indices_to_remove, reverse=True):
                self.documents.pop(i)
                if len(self.vectors) > 0:
                    self.vectors = np.delete(self.vectors, i, axis=0)
                
            self._save_data()
            logger.info(f"🗑️ {len(indices_to_remove)} doc(s) antigo(s) removidos para {thread_id}")
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
            
            # Garantir consistência dos metadados para filtros
            # 'traveler' e 'primary_traveler_name' são sinônimos — normalizar os dois
            traveler = metadata.get("traveler") or metadata.get("primary_traveler_name")
            full_metadata = {
                "filename": metadata.get("filename"),
                "thread_id": metadata.get("thread_id"),
                "trip_id": metadata.get("trip_id"),
                "mimetype": metadata.get("mimetype"),
                "document_type": metadata.get("document_type", "geral"),
                "primary_traveler_name": traveler,
                "traveler": traveler,           # <- campo que parsers usam
                "uploaded_by": metadata.get("thread_id"),  # quem fez upload
                "drive_link": metadata.get("drive_link"),
                "segment_info": metadata.get("segment_info")
            }
            
            self.documents.append({
                "text": text,
                "metadata": full_metadata
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

    def add_documents_batch(self, docs_list: List[Dict[str, Any]]):
        """Adiciona múltiplos documentos de uma vez, gerando embeddings e salvando apenas no final (Otimização de I/O)."""
        if not docs_list:
            return
            
        try:
            logger.info(f"📥 Indexando lote de {len(docs_list)} documentos...")
            texts = [d["text"] for d in docs_list]
            
            # Gerar embeddings em batch (mais eficiente que um por um se suportado, 
            # mas OpenAI embeddings query usually is singular. Let's use embed_documents)
            vectors = self.embeddings.embed_documents(texts)
            
            for i, doc in enumerate(docs_list):
                metadata = doc["metadata"]
                traveler = metadata.get("traveler") or metadata.get("primary_traveler_name")
                
                full_metadata = {
                    "filename": metadata.get("filename"),
                    "thread_id": metadata.get("thread_id"),
                    "trip_id": metadata.get("trip_id"),
                    "mimetype": metadata.get("mimetype"),
                    "document_type": metadata.get("document_type", "geral"),
                    "primary_traveler_name": traveler,
                    "traveler": traveler,
                    "uploaded_by": metadata.get("thread_id"),
                    "drive_link": metadata.get("drive_link"),
                    "segment_info": metadata.get("segment_info")
                }
                
                self.documents.append({
                    "text": texts[i],
                    "metadata": full_metadata
                })
                
                if len(self.vectors) == 0:
                    self.vectors = np.array([vectors[i]])
                else:
                    self.vectors = np.vstack([self.vectors, vectors[i]])
                    
            # Persistir APENAS UMA VEZ ao final do lote
            self._save_data()
            logger.info(f"✅ Lote de {len(docs_list)} documentos indexado com sucesso.")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar lote de documentos: {e}")
            return False
            
    def _cosine_similarity(self, v1: np.ndarray, v2_matrix: np.ndarray) -> np.ndarray:
        """Calcula a similaridade de cosseno manual usando NumPy"""
        # v1 shape: (1, dim), v2_matrix shape: (N, dim)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2_matrix, axis=1)
        
        dot_product = np.dot(v2_matrix, v1.T).flatten()
        return dot_product / (norm_v1 * norm_v2)

    def query(self, query_text: str, thread_id: str, k: int = 10) -> str:
        """Busca semântica filtrada por viagem ativa do usuário"""
        if not self.documents:
            return "Você ainda não enviou nenhum documento de viagem."
            
        try:
            logger.info(f"🔍 Buscando no RAG: '{query_text}' (Usuario: {thread_id})")
            
            from app.services.user_service import UserService
            user_service = UserService()
            thread_id = user_service.normalize_phone(thread_id)
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
                doc = self.documents[idx]
                m = doc["metadata"]
                source_info = f"[Fonte: {m.get('filename', 'Doc')}"
                if m.get('primary_traveler_name'):
                    source_info += f" | Passageiro: {m.get('primary_traveler_name')}"
                if m.get('drive_link'):
                    source_info += f" | Link: {m.get('drive_link')}"
                source_info += "]"
                
                results.append(f"{source_info}\n{doc['text']}")
                
            return "\n---\n".join(results)
            
        except Exception as e:
            logger.error(f"❌ Erro na consulta ao RAG: {e}")
            return f"Erro ao acessar documentos: {str(e)}"

    def list_user_documents(self, thread_id: str, document_type: str = None) -> List[str]:
        """Lista nomes de arquivos enviados para a viagem atual do usuário ou para o próprio usuário"""
        from app.services.user_service import UserService
        user_service = UserService()
        thread_id = user_service.normalize_phone(thread_id)
        active_trip = user_service.get_active_trip(thread_id)
        
        filenames = []
        for doc in self.documents:
            m = doc["metadata"]
            m_trip = m.get("trip_id")
            m_thread = m.get("thread_id")
            m_type = m.get("document_type", "").lower()
            m_traveler = m.get("primary_traveler_name", "")
            
            if (active_trip and m_trip == active_trip) or m_thread == thread_id:
                # Aplicar filtro de tipo se fornecido
                if document_type and m_type != document_type.lower():
                    continue
                
                fname = m.get("filename", "documento")
                display_name = f"*{fname}*"
                
                info_parts = []
                if m_traveler:
                    info_parts.append(f"Passageiro: {m_traveler}")
                if m.get("segment_info"):
                    info_parts.append(f"Trecho: {m['segment_info']}")
                    
                if info_parts:
                    display_name += " - " + " | ".join(info_parts)
                
                filenames.append(display_name)
                    
        return sorted(list(set(filenames)))

    def assign_trip_to_user_documents(self, thread_id: str, trip_id: str) -> int:
        """
        Retroativamente vincula todos os documentos de um usuário a um trip_id específico.
        Útil quando um convidado envia documentos antes de ser formalmente autorizado para a viagem.
        Sobrescreve qualquer trip_id anterior para garantir que todos os docs fiquem na mesma 'pasta' lógica.
        """
        try:
            self._load_data()
            count = 0
            # Inicializa UserService localmente para normalização
            from app.services.user_service import UserService
            user_svc = UserService()
            
            for doc in self.documents:
                m = doc["metadata"]
                # Normaliza ambos para comparação segura
                if user_svc.normalize_phone(m.get("thread_id")) == user_svc.normalize_phone(thread_id):
                    if m.get("trip_id") != trip_id:
                        m["trip_id"] = trip_id
                        count += 1
            
            if count > 0:
                self._save_data()
                logger.info(f"🔗 {count} documentos de {thread_id} foram recalibrados para a trip {trip_id}")
            
            return count
        except Exception as e:
            logger.error(f"❌ Erro ao vincular documentos retroativamente: {e}")
            return 0
