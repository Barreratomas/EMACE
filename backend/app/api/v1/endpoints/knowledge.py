import shutil
import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from app.api.deps import get_current_user, RoleChecker, get_tenant_owner_id
from app.core.database.models import User
from app.core.rag.ingestion import ingestion_service

router = APIRouter()

# Solo administradores o vendedores pueden gestionar conocimiento
allowed_roles = RoleChecker(["admin", "vendor"])

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
        
        # Procesar ingesta
        ingestion_service.ingest_file(file_path, user_id=owner_id)
        
        return {"message": f"Archivo '{file.filename}' procesado e indexado correctamente."}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_CODE,
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listando documentos: {str(e)}"
        )

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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error eliminando documento: {str(e)}"
        )
