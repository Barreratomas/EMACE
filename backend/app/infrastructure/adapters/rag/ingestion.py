import os
from typing import List, Optional, Set
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse
import logging

from app.infrastructure.adapters.vector.client import get_qdrant_client, init_collections
from app.infrastructure.adapters.rag.embeddings import get_embeddings
from app.domain.ports.repositories import IKnowledgePort

class IngestionService(IKnowledgePort):
    def __init__(self):
        self.client = get_qdrant_client()
        self.embeddings = get_embeddings()
        self.collection_name = "knowledge_base"
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )

    logger = logging.getLogger(__name__)

    def ingest_file(self, file_path: str, user_id: Optional[int] = None):
        """
        Lee un archivo, lo divide en chunks y lo guarda en Qdrant.
        Soporta: .pdf, .txt, .md
        """
        print(f"📄 Procesando archivo: {file_path}")
        file_size_bytes = os.path.getsize(file_path)

        if file_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith(".md"):
            loader = TextLoader(file_path, encoding="utf-8") # TextLoader suele ir bien para MD simple
        elif file_path.endswith(".txt"):
            loader = TextLoader(file_path, encoding="utf-8")
        else:
            raise ValueError(f"Formato no soportado: {file_path}")
            
        docs = loader.load()
        for d in docs:
            if not getattr(d, "metadata", None):
                d.metadata = {}
            d.metadata["file_size_bytes"] = file_size_bytes
        print(f"   -> Documento cargado. Páginas/Secciones: {len(docs)}")

        # 2. Dividir en Chunks
        chunks = self.text_splitter.split_documents(docs)
        print(f"   -> Dividido en {len(chunks)} fragmentos.")

        # 3. Vectorizar y Guardar
        self._upsert_chunks(chunks, source=os.path.basename(file_path), user_id=user_id)
        print("✅ Ingesta completada exitosamente.")

    def ingest_text(self, text: str, source: str = "manual_input", user_id: Optional[int] = None):
        """
        Ingesta texto directo (raw string).
        """
        doc = Document(page_content=text, metadata={"source": source})
        chunks = self.text_splitter.split_documents([doc])
        self._upsert_chunks(chunks, source=source, user_id=user_id)

    def _upsert_chunks(self, chunks: List[Document], source: str, user_id: Optional[int] = None):
        """
        Genera embeddings y sube a Qdrant.
        """
        texts = [d.page_content for d in chunks]
        metadatas = [d.metadata for d in chunks]
        
        # Generar embeddings
        print("   -> Generando embeddings (puede tardar un poco)...")
        vectors = self.embeddings.embed_documents(texts)
        
        # Preparar puntos para Qdrant
        points = []
        import uuid
        for i, (text, vector, meta) in enumerate(zip(texts, vectors, metadatas)):
            # Asegurar que metadata sea plana o compatible
            payload = {
                "page_content": text,
                "source": source,
                **meta
            }
            if user_id is not None:
                payload["user_id"] = user_id
            
            points.append(models.PointStruct(
                id=str(uuid.uuid4()), # ID único aleatorio
                vector=vector,
                payload=payload
            ))
            
        # Subir en batch
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
        except UnexpectedResponse as e:
            msg = str(e)
            if "Collection `knowledge_base` doesn't exist" in msg:
                try:
                    self.logger.info(
                        {
                            "event": "rag.upsert.collection_missing",
                            "collection": self.collection_name,
                            "points": len(points),
                        }
                    )
                except Exception:
                    pass
                # Crear colección de forma perezosa e intentar de nuevo
                init_collections()
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
            else:
                raise
        print(f"   -> {len(points)} vectores guardados en '{self.collection_name}'.")

    def get_vendor_usage_bytes(self, user_id: int) -> int:
        """
        Calcula el uso aproximado en bytes de conocimiento para un vendor,
        sumando file_size_bytes por cada documento (source) único.
        """
        total = 0
        seen_sources: Set[str] = set()

        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value=user_id)
                )
            ]
        )

        offset = None
        while True:
            points, offset = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=query_filter,
                limit=256,
                with_payload=True,
                with_vectors=False,
                offset=offset
            )
            if not points:
                break

            for p in points:
                payload = getattr(p, "payload", {}) or {}
                src = payload.get("source")
                if not src or src in seen_sources:
                    continue
                size = payload.get("file_size_bytes")
                if isinstance(size, (int, float)):
                    total += int(size)
                    seen_sources.add(src)

            if offset is None:
                break

        return total

    def list_documents(self, user_id: Optional[int] = None):
        """
        Lista documentos únicos ingeridos para un usuario.
        """
        try:
            filter_query = None
            if user_id is not None:
                filter_query = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="user_id",
                            match=models.MatchValue(value=user_id)
                        )
                    ]
                )
            points, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filter_query,
                limit=100,
                with_payload=True,
                with_vectors=False
            )
            sources = {}
            for p in points:
                payload = getattr(p, "payload", {}) or {}
                src = payload.get("source")
                if src and src not in sources:
                    sources[src] = {
                        "name": src,
                        "id": getattr(p, "id", None),
                        "created_at": payload.get("created_at", "N/A")
                    }
            return list(sources.values())
        except Exception as e:
            # Si la colección aún no existe, devolvemos lista vacía en lugar de 500
            msg = str(e)
            if isinstance(e, UnexpectedResponse) and "Collection `knowledge_base` doesn't exist" in msg:
                try:
                    self.logger.info(
                        {
                            "event": "rag.list_documents.collection_missing",
                            "user_id": user_id,
                            "collection": self.collection_name,
                        }
                    )
                except Exception:
                    pass
                return []
            try:
                self.logger.error(
                    {
                        "event": "rag.list_documents.error",
                        "user_id": user_id,
                        "error": msg[:500],
                    },
                    exc_info=True,
                )
            except Exception:
                pass
            raise

    def delete_document(self, source_name: str, user_id: Optional[int] = None):
        """
        Elimina todos los puntos asociados a una fuente y usuario.
        """
        conditions = [
            models.FieldCondition(
                key="source",
                match=models.MatchValue(value=source_name)
            )
        ]
        if user_id:
            conditions.append(
                models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value=user_id)
                )
            )
            
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(must=conditions)
            )
        )
        return True

# Instancia global para uso fácil
ingestion_service = IngestionService()
