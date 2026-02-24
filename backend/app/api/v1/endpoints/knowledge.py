import shutil
import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from app.api.deps import get_current_user, RoleChecker, get_tenant_owner_id
from app.core.database.models import User
from app.core.rag.ingestion import ingestion_service
from app.core.config import settings
import logging

router = APIRouter()

# Solo administradores o vendedores pueden gestionar conocimiento
allowed_roles = RoleChecker(["admin", "vendor"])

logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_knowledge(
    file: UploadFile = File(...),
    current_user: User = Depends(allowed_roles)
):
    """
    Sube un archivo (PDF, MD, TXT) para ser procesado e indexado en la base de conocimiento.
    """
    allowed_extensions = [".pdf", ".md", ".txt"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extensión de archivo no permitida. Use: {', '.join(allowed_extensions)}"
        )

    # Crear directorio temporal si no existe
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    
    owner_id = get_tenant_owner_id(current_user)
    file_path = os.path.join(temp_dir, f"{owner_id}_{file.filename}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size_bytes = os.path.getsize(file_path)
        max_bytes = settings.KNOWLEDGE_MAX_MB_PER_VENDOR * 1024 * 1024
        current_usage = ingestion_service.get_vendor_usage_bytes(owner_id)

        if current_usage + file_size_bytes > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Se alcanzó el límite de {settings.KNOWLEDGE_MAX_MB_PER_VENDOR}MB de base de conocimiento para este tenant. Elimina documentos antiguos antes de subir nuevos."
            )

        # Procesar ingesta
        ingestion_service.ingest_file(file_path, user_id=owner_id)
        
        return {"message": f"Archivo '{file.filename}' procesado e indexado correctamente."}
    except HTTPException:
        raise
    except Exception as e:
        try:
            logger.error(
                {
                    "event": "knowledge.upload.error",
                    "owner_id": owner_id,
                    "filename": file.filename if file and file.filename else None,
                    "error": str(e)[:500],
                },
                exc_info=True,
            )
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando el archivo: {str(e)}"
        )
    finally:
        # Limpiar archivo temporal
        if os.path.exists(file_path):
            os.remove(file_path)

@router.get("/documents")
async def list_knowledge_documents(
    current_user: User = Depends(allowed_roles)
):
    """
    Lista los documentos ingeridos por el usuario actual.
    """
    try:
        owner_id = get_tenant_owner_id(current_user)
        docs = ingestion_service.list_documents(user_id=owner_id)
        return docs
    except Exception as e:
        try:
            logger.error(
                {
                    "event": "knowledge.list.error",
                    "owner_id": get_tenant_owner_id(current_user),
                    "error": str(e)[:500],
                },
                exc_info=True,
            )
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listando documentos: {str(e)}"
        )


@router.get("/usage")
async def get_knowledge_usage(
    current_user: User = Depends(allowed_roles),
):
    """
    Devuelve el uso actual de la base de conocimiento para el vendor,
    en bytes y MB, junto con el límite configurado.
    """
    owner_id = get_tenant_owner_id(current_user)
    used_bytes = ingestion_service.get_vendor_usage_bytes(owner_id)
    max_bytes = settings.KNOWLEDGE_MAX_MB_PER_VENDOR * 1024 * 1024
    used_mb = round(used_bytes / (1024 * 1024), 2)
    max_mb = settings.KNOWLEDGE_MAX_MB_PER_VENDOR
    ratio = used_bytes / max_bytes if max_bytes > 0 else 0.0
    return {
        "used_bytes": used_bytes,
        "used_mb": used_mb,
        "max_bytes": max_bytes,
        "max_mb": max_mb,
        "usage_ratio": ratio,
    }


@router.delete("/documents/{source_name}")
async def delete_knowledge_document(
    source_name: str,
    current_user: User = Depends(allowed_roles)
):
    """
    Elimina un documento específico de la base de conocimiento del usuario.
    """
    try:
        owner_id = get_tenant_owner_id(current_user)
        ingestion_service.delete_document(source_name, user_id=owner_id)
        return {"message": f"Documento '{source_name}' eliminado correctamente."}
    except Exception as e:
        try:
            logger.error(
                {
                    "event": "knowledge.delete.error",
                    "owner_id": owner_id,
                    "source_name": source_name,
                    "error": str(e)[:500],
                },
                exc_info=True,
            )
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error eliminando documento: {str(e)}"
        )
