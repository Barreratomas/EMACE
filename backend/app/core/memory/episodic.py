import uuid
from datetime import datetime
from qdrant_client.http import models
from app.core.vector.client import get_qdrant_client
from app.core.rag.embeddings import get_embeddings

class EpisodicMemory:
    def __init__(self):
        self._client = None
        self._embeddings = None
        self.collection_name = "knowledge_base" # Usamos la base de conocimiento general con metadata

    @property
    def client(self):
        if self._client is None:
            print("🔍 [EpisodicMemory] Accessing client property (Lazy Load)")
            self._client = get_qdrant_client()
        return self._client

    @property
    def embeddings(self):
        if self._embeddings is None:
            print("🔍 [EpisodicMemory] Accessing embeddings property (Lazy Load)")
            self._embeddings = get_embeddings()
        return self._embeddings

    def remember_interaction(self, user_input: str, agent_response: str, user_id: int):
        """
        Guarda un par de interacción (Usuario -> Agente) como memoria episódica.
        """
        text_to_embed = f"Usuario: {user_input}\nAgente: {agent_response}"
        vector = self.embeddings.embed_query(text_to_embed)
        
        payload = {
            "page_content": text_to_embed,
            "source": "episodic_memory",
            "user_input": user_input,
            "agent_response": agent_response,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "type": "chat_log"
        }
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload=payload
                )
            ]
        )
        print("🧠 Memoria episódica guardada.")

    def recall_similar_interactions(self, query: str, user_id: int, limit: int = 3) -> str:
        """
        Recupera interacciones pasadas similares para un usuario específico.
        """
        query_vector = self.embeddings.embed_query(query)
        
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="type",
                        match=models.MatchValue(value="chat_log")
                    ),
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=user_id)
                    )
                ]
            ),
            limit=limit
        ).points
        
        if not results:
            return ""
            
        context = "### MEMORIA EPISÓDICA (Chats anteriores):\n"
        for hit in results:
            context += f"- {hit.payload['page_content']} (Hace: {hit.payload['timestamp']})\n"
            
        return context

episodic_memory = EpisodicMemory()
