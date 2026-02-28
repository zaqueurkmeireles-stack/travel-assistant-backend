"""
Google Drive Service - Gerencia o salvamento de fotos e vídeos da viagem.
"""

import io
import json
import os
from typing import Optional, Dict, Any
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from app.config import settings
from loguru import logger

class GoogleDriveService:
    """Service para integração com Google Drive (Arquivamento de Mídia)"""
    
    def __init__(self):
        self.creds = self._load_credentials()
        if self.creds:
            self.service = build('drive', 'v3', credentials=self.creds)
            logger.info("✅ Google Drive Service inicializado")
        else:
            self.service = None
            logger.warning("⚠️ Google Drive Service desativado (Credenciais ausentes)")

    def _load_credentials(self):
        """Carrega credenciais a partir do JSON no config"""
        creds_json = settings.GOOGLE_DRIVE_CREDENTIALS_JSON
        if not creds_json:
            return None
        
        try:
            # Pode ser um caminho de arquivo ou o JSON direto
            if creds_json.startswith('{'):
                info = json.loads(creds_json)
                return service_account.Credentials.from_service_account_info(
                    info, scopes=['https://www.googleapis.com/auth/drive.file']
                )
            elif os.path.exists(creds_json):
                return service_account.Credentials.from_service_account_file(
                    creds_json, scopes=['https://www.googleapis.com/auth/drive.file']
                )
        except Exception as e:
            logger.error(f"Erro ao carregar credenciais do Google Drive: {e}")
        return None

    def get_or_create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """Busca ou cria uma pasta no Drive"""
        if not self.service: return None
        
        parent_id = parent_id or settings.GOOGLE_DRIVE_ROOT_FOLDER_ID
        
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
            
        try:
            results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            items = results.get('files', [])
            
            if items:
                return items[0]['id']
            
            # Criar se não existir
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id:
                file_metadata['parents'] = [parent_id]
                
            file = self.service.files().create(body=file_metadata, fields='id').execute()
            logger.info(f"📁 Pasta criada no Drive: {folder_name} (ID: {file.get('id')})")
            return file.get('id')
        except Exception as e:
            logger.error(f"Erro ao gerenciar pasta no Drive: {e}")
        return None

    def upload_file(self, file_content: bytes, filename: str, mimetype: str, folder_id: str) -> Optional[str]:
        """Faz upload de um arquivo para uma pasta específica"""
        if not self.service: return None
        
        try:
            file_metadata = {
                'name': filename,
                'parents': [folder_id]
            }
            media = MediaIoBaseUpload(io.BytesIO(file_content), mimetype=mimetype, resumable=True)
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            logger.info(f"📤 Arquivo enviado para o Drive: {filename} (ID: {file.get('id')})")
            return file.get('id')
        except Exception as e:
            logger.error(f"Erro no upload para o Drive: {e}")
        return None

    def get_trip_media_folder(self, user_id: str, trip_name: str) -> Optional[str]:
        """Garante a estrutura: Seven Assistant -> [Viagem]"""
        # 1. Pasta Raiz (Seven Assistant)
        root_id = self.get_or_create_folder("Seven Assistant Media")
        
        # 2. Pasta da Viagem específica
        trip_folder_id = self.get_or_create_folder(trip_name, parent_id=root_id)
        
        return trip_folder_id
