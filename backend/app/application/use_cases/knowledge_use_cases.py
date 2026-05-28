import os
import shutil
from typing import List, Dict, Any, Optional
from fastapi import UploadFile, HTTPException, status
from app.domain.models import AuditLog
from app.domain.ports.repositories import IKnowledgePort, IAuditRepository
from app.domain.ports.background_jobs import IBackgroundJobPort
from app.infrastructure.config import settings

class KnowledgeUseCases:
    def __init__(
        self, 
        knowledge_port: IKnowledgePort,
        audit_repo: IAuditRepository,
        background_job_port: Optional[IBackgroundJobPort] = None
    ):
        self.knowledge_port = knowledge_port
        self.audit_repo = audit_repo
        self.background_job_port = background_job_port

    async def upload_document(self, session: Any, file: UploadFile, user_id: int) -> Dict[str, Any]:
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

            # Si tenemos un puerto de tareas en segundo plano, encolamos y delegamos la eliminación al worker
            if self.background_job_port:
                task_id = await self.background_job_port.enqueue_task(
                    "ingest_document_task",
                    file_path=file_path,
                    user_id=user_id
                )
                
                # Log audit
                await self.audit_repo.save_log(session, AuditLog(
                    user_id=user_id,
                    agent_name="System",
                    action="KNOWLEDGE_UPLOAD_STARTED",
                    details=f"Subida de documento iniciada: {file.filename} (Task: {task_id})"
                ))

                return {
                    "message": f"Archivo '{file.filename}' recibido. Procesando en segundo plano...",
                    "task_id": task_id,
                    "status": "processing"
                }

            # Fallback a procesamiento síncrono (legacy/test)
            self.knowledge_port.ingest_file(file_path, user_id=user_id)
            
            # Log audit
            await self.audit_repo.save_log(session, AuditLog(
                user_id=user_id,
                agent_name="System",
                action="KNOWLEDGE_UPLOADED",
                details=f"Documento subido y procesado: {file.filename}"
            ))

            return {"message": f"Archivo '{file.filename}' procesado correctamente."}
        except Exception as e:
            # Si algo falla antes de encolar, nos aseguramos de limpiar el archivo
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e
        # Eliminamos el finally que borraba el archivo, ya que ahora el worker se encarga de eso
        # si se encoló exitosamente. Si no se encoló (fallback), se borra arriba o aquí abajo:
        finally:
            if not self.background_job_port and os.path.exists(file_path):
                os.remove(file_path)

    async def list_documents(self, user_id: int) -> List[Dict[str, Any]]:
        return self.knowledge_port.list_documents(user_id=user_id)

    async def get_usage(self, user_id: int) -> Dict[str, Any]:
        usage_bytes = self.knowledge_port.get_vendor_usage_bytes(user_id)
        max_bytes = settings.KNOWLEDGE_MAX_MB_PER_VENDOR * 1024 * 1024
        return {
            "used_bytes": usage_bytes,
            "used_mb": round(usage_bytes / (1024 * 1024), 2),
            "max_bytes": max_bytes,
            "max_mb": settings.KNOWLEDGE_MAX_MB_PER_VENDOR,
            "usage_ratio": round(usage_bytes / max_bytes, 4) if max_bytes > 0 else 0,
            "percentage": round((usage_bytes / max_bytes) * 100, 2) if max_bytes > 0 else 0
        }

    async def delete_document(self, session: Any, user_id: int, source_name: str) -> Dict[str, bool]:
        success = self.knowledge_port.delete_document(user_id, source_name)
        
        if success:
            # Log audit
            await self.audit_repo.save_log(session, AuditLog(
                user_id=user_id,
                agent_name="System",
                action="KNOWLEDGE_DELETED",
                details=f"Documento eliminado: {source_name}"
            ))

        return {"success": success}
