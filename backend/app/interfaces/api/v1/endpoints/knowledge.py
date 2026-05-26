from typing import List
from fastapi import APIRouter, Depends, UploadFile, File
from app.interfaces.api.deps import get_current_user, RoleChecker, get_tenant_owner_id, get_background_job_port
from app.domain.models import User
from app.domain.ports.background_jobs import IBackgroundJobPort
from app.infrastructure.adapters.rag.ingestion import ingestion_service
from app.application.use_cases.knowledge_use_cases import KnowledgeUseCases

router = APIRouter()
allowed_roles = RoleChecker(["admin", "vendor"])

def get_knowledge_use_cases(
    background_job_port: IBackgroundJobPort = Depends(get_background_job_port)
) -> KnowledgeUseCases:
    return KnowledgeUseCases(
        knowledge_port=ingestion_service,
        background_job_port=background_job_port
    )

@router.post("/upload")
async def upload_knowledge(
    file: UploadFile = File(...),
    current_user: User = Depends(allowed_roles),
    use_cases: KnowledgeUseCases = Depends(get_knowledge_use_cases)
):
    """Sube y procesa documentos (PDF, TXT, MD) para la base de conocimiento RAG"""
    owner_id = get_tenant_owner_id(current_user)
    return await use_cases.upload_document(file, owner_id)

@router.get("/documents")
async def list_knowledge_documents(
    current_user: User = Depends(allowed_roles),
    use_cases: KnowledgeUseCases = Depends(get_knowledge_use_cases)
):
    """Lista todos los documentos ingeridos en la base de conocimiento del vendor"""
    owner_id = get_tenant_owner_id(current_user)
    return await use_cases.list_documents(owner_id)

@router.get("/usage")
async def get_knowledge_usage(
    current_user: User = Depends(allowed_roles),
    use_cases: KnowledgeUseCases = Depends(get_knowledge_use_cases)
):
    """Obtiene el uso actual de almacenamiento de la base de conocimiento"""
    owner_id = get_tenant_owner_id(current_user)
    return await use_cases.get_usage(owner_id)

@router.delete("/documents/{source_name}")
async def delete_knowledge_document(
    source_name: str,
    current_user: User = Depends(allowed_roles),
    use_cases: KnowledgeUseCases = Depends(get_knowledge_use_cases)
):
    """Elimina un documento específico y sus vectores asociados de la base de conocimiento"""
    owner_id = get_tenant_owner_id(current_user)
    return await use_cases.delete_document(owner_id, source_name)
