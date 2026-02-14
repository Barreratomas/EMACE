import os
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader
from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.core.vector.client import get_qdrant_client
from app.core.rag.embeddings import get_embeddings

class IngestionService:
    def __init__(self):
        self.client = get_qdrant_client()
        self.embeddings = get_embeddings()
        self.collection_name = "knowledge_base"
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )

    def ingest_file(self, file_path: str, user_id: Optional[int] = None):
        """
        Lee un archivo, lo divide en chunks y lo guarda en Qdrant.
        Soporta: .pdf, .txt, .md
        """
        print(f"📄 Procesando archivo: {file_path}")
        
        # 1. Cargar Documento
        if file_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith(".md"):
            loader = TextLoader(file_path, encoding="utf-8") # TextLoader suele ir bien para MD simple
        elif file_path.endswith(".txt"):
            loader = TextLoader(file_path, encoding="utf-8")
        else:
            raise ValueError(f"Formato no soportado: {file_path}")
            
        docs = loader.load()
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
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        print(f"   -> {len(points)} vectores guardados en '{self.collection_name}'.")

# Instancia global para uso fácil
ingestion_service = IngestionService()
