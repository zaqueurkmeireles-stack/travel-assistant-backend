import sqlite3
import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from loguru import logger
from app.config import settings

class IdempotencyService:
    """
    Serviço de Idempotência e Gestão de Jobs.
    Garante que a mesma mensagem não seja processada múltiplas vezes.
    Caminho do Job: RECEIVED -> PROCESSING -> SUCCEEDED/FAILED -> RESPONDED
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IdempotencyService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized: return
        self.db_path = os.path.join(os.path.dirname(settings.CHROMA_DB_PATH), "idempotency.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
        self._initialized = True
        logger.info(f"🛡️ IdempotencyService inicializado (SQLite: {self.db_path})")

    def _init_db(self):
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    idempotency_key TEXT PRIMARY KEY,
                    message_id TEXT,
                    chat_id TEXT,
                    status TEXT, -- RECEIVED, PROCESSING, SUCCEEDED, FAILED, RESPONDED
                    payload TEXT,
                    response TEXT,
                    error_msg TEXT,
                    correlation_id TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON jobs(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_id ON jobs(chat_id)")

    def generate_key(self, chat_id: str, message_id: Optional[str], message_text: str = "", media_hash: str = "") -> str:
        """Gera uma chave determinística caso o message_id falhe."""
        if message_id:
            return message_id
        
        # Fallback determinístico
        raw = f"{chat_id}:{message_text[:100]}:{media_hash}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def check_and_register(self, idempotency_key: str, chat_id: str, message_id: Optional[str], payload: Dict) -> Optional[str]:
        """
        Verifica se a chave já existe. 
        Se não existir, registra como RECEIVED e retorna None.
        Se existir e estiver SUCCEEDED/RESPONDED, retorna a resposta salva.
        Se estiver PROCESSING, retorna 'PROCESSING'.
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT status, response FROM jobs WHERE idempotency_key = ?", (idempotency_key,))
                row = cursor.fetchone()
                
                if row:
                    status, response = row
                    logger.warning(f"♻️ Idempotência: Chave {idempotency_key} já existe com status {status}")
                    return status if status == "PROCESSING" else (response or status)
                
                # Registrar novo
                now = datetime.now().isoformat()
                import uuid
                correlation_id = str(uuid.uuid4())
                conn.execute(
                    "INSERT INTO jobs (idempotency_key, message_id, chat_id, status, payload, correlation_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (idempotency_key, message_id, chat_id, "RECEIVED", json.dumps(payload), correlation_id, now, now)
                )
                return None
        except Exception as e:
            logger.error(f"❌ Erro no cache de idempotência: {e}")
            return None

    def update_status(self, idempotency_key: str, status: str, response: Optional[str] = None, error_msg: Optional[str] = None):
        """Atualiza o status do job."""
        try:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                now = datetime.now().isoformat()
                conn.execute(
                    "UPDATE jobs SET status = ?, response = ?, error_msg = ?, updated_at = ? WHERE idempotency_key = ?",
                    (status, response, error_msg, now, idempotency_key)
                )
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar status de idempotência: {e}")

    def get_correlation_id(self, idempotency_key: str) -> str:
        """Recupera o correlation_id gerado para o job."""
        try:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT correlation_id FROM jobs WHERE idempotency_key = ?", (idempotency_key,))
                row = cursor.fetchone()
                return row[0] if row else "unknown"
        except:
            return "unknown"

    def cleanup_old_jobs(self, days: int = 7):
        """Remove jobs antigos para evitar crescimento infinito do SQLite."""
        try:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                count = conn.execute("DELETE FROM jobs WHERE created_at < ?", (cutoff,)).rowcount
                if count > 0:
                    logger.info(f"🧹 Cleanup Idempotency: {count} registros removidos.")
        except Exception as e:
            logger.error(f"❌ Erro no cleanup de idempotência: {e}")

def get_idempotency():
    return IdempotencyService()
