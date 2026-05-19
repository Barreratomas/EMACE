import os
import shutil
from typing import List, Dict, Any
from fastapi import UploadFile, HTTPException, status
from app.domain.ports.repositories import IKnowledgePort
from app.infrastructure.config import settings

class KnowledgeUseCases:
    def __init__(self, knowledge_port: IKnowledgePort):
        self.knowledge_port = knowledge_port

    async def upload_document(self, file: UploadFile, user_id: int) -> Dict[str, str]:
        allowed_extensions = [".pdf", ".md", ".txt"]
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Extensión de archivo no permitida. Use: {', '.join(allowed_extensions)}"
            )

        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, f"{user_id}_{file.filename}")
        
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            file_size_bytes = os.path.getsize(file_path)
            max_bytes = settings.KNOWLEDGE_MAX_MB_PER_VENDOR * 1024 * 1024
            current_usage = self.knowledge_port.get_vendor_usage_bytes(user_id)

            if current_usage + file_size_bytes > max_bytes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Se alcanzó el límite de {settings.KNOWLEDGE_MAX_MB_PER_VENDOR}MB. Elimina documentos antiguos."
                )

            # Ingestión (esto es síncrono en el servicio original, lo mantenemos así o lo envolvemos en un thread si es necesario)
            self.knowledge_port.ingest_file(file_path, user_id=user_id)
            
            return {"message": f"Archivo '{file.filename}' procesado correctamente."}
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    async def list_documents(self, user_id: int) -> List[Dict[str, Any]]:
        return self.knowledge_port.list_documents(user_id=user_id)

    async def delete_document(self, user_id: int, source_name: str) -> Dict[str, bool]:
        success = self.knowledge_port.delete_document(user_id, source_name)
        return {"success": success}
