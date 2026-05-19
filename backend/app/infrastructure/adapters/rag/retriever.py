from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.infrastructure.adapters.vector.client import get_qdrant_client
from app.infrastructure.adapters.rag.embeddings import get_embeddings

class HybridRetriever:
    def __init__(self):
        self.client = get_qdrant_client()
        self.embeddings = get_embeddings()

    def search(self, query: str, collection: str = "knowledge_base", limit: int = 5, score_threshold: float = 0.4, user_id: Optional[int] = None) -> List[Dict]:
        """
        Búsqueda semántica simple.
        Retorna lista de dicts con: content, source, score.
        Si se proporciona user_id, se filtra por ese ID (Data Isolation).
        """
        # 1. Generar vector del query
        query_vector = self.embeddings.embed_query(query)
        
        # 1.5 Construir filtro
        query_filter = None
        if user_id is not None:
             query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=user_id)
                    )
                ]
            )

        # 2. Buscar en Qdrant
        results = self.client.query_points(
            collection_name=collection,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            score_threshold=score_threshold
        ).points
        
        # 3. Formatear respuesta
        formatted_results = []
        for hit in results:
            formatted_results.append({
                "content": hit.payload.get("page_content", ""),
                "source": hit.payload.get("source", "unknown"),
                "score": hit.score,
                "metadata": {k:v for k,v in hit.payload.items() if k not in ["page_content", "source"]}
            })
            
        return formatted_results

    def search_lessons_learned(self, query: str, limit: int = 3, user_id: Optional[int] = None) -> str:
        """
        Busca lecciones aprendidas relevantes y las formatea como string de contexto.
        """
        results = self.search(query, collection="lessons_learned", limit=limit, score_threshold=0.5, user_id=user_id)
        
        if not results:
            return ""
            
        context = "### LECCIONES APRENDIDAS (Evitar errores previos):\n"
        for r in results:
            context += f"- {r['content']} (Score: {r['score']:.2f})\n"
        
        return context

retriever = HybridRetriever()
