from qdrant_client import QdrantClient
from qdrant_client.http import models
import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_PATH = os.getenv("QDRANT_PATH")

# Prioritize local path if set, otherwise URL, otherwise default URL
# We will initialize client lazily to avoid import-time connection errors
_client_instance = None

def get_qdrant_client():
    global _client_instance
    print(f"🔍 [get_qdrant_client] Start. Existing instance: {_client_instance is not None}")
    if _client_instance is not None:
        return _client_instance

    print(f"🔍 [get_qdrant_client] Initializing new client. PATH={QDRANT_PATH}, URL={QDRANT_URL}")
    if QDRANT_PATH:
        try:
            # Ensure directory exists
            print(f"🔍 [get_qdrant_client] Using local path: {QDRANT_PATH}")
            os.makedirs(QDRANT_PATH, exist_ok=True)
            _client_instance = QdrantClient(path=QDRANT_PATH)
            print(f"✅ [get_qdrant_client] Connected to local Qdrant at: {QDRANT_PATH}")
        except Exception as e:
            print(f"❌ [get_qdrant_client] Error initializing local client: {e}")
            raise e
    else:
        url = QDRANT_URL if QDRANT_URL else "http://localhost:6333"
        try:
            print(f"🔍 [get_qdrant_client] Connecting to URL: {url}")
            _client_instance = QdrantClient(url=url)
            print(f"✅ [get_qdrant_client] Connected to Qdrant URL: {url}")
        except Exception as e:
            print(f"❌ [get_qdrant_client] Error connecting to Qdrant at {url}: {e}")
            raise e
            
    return _client_instance

# Deprecated: direct access to client. Use get_qdrant_client() instead.
# For backward compatibility with existing code that might import client directly
# We create a proxy or just initialize it here if absolutely necessary, but better to avoid it.
# client = get_qdrant_client() # REMOVED to prevent import side-effects

# Función para inicializar colecciones (idempotente)
def init_collections():
    client = get_qdrant_client()
    collections = ["knowledge_base", "lessons_learned"]
    existing = [c.name for c in client.get_collections().collections]
    
    for col in collections:
        if col not in existing:
            # all-MiniLM-L6-v2 output dimension is 384
            client.create_collection(
                collection_name=col,
                vectors_config={"size": 384, "distance": "Cosine"}
            )
            print(f"Colección '{col}' creada.")
        else:
            print(f"Colección '{col}' ya existe.")

    # Crear índices para optimización (Fase 9.4)
    # Indices para knowledge_base (Memoria Episódica)
    try:
        # Index para user_id (Multi-Tenancy crítico)
        client.create_payload_index(
            collection_name="knowledge_base",
            field_name="user_id",
            field_schema=models.PayloadSchemaType.INTEGER
        )
        print("Index creado para 'user_id' en knowledge_base.")
    except Exception as e:
        print(f"Nota sobre index user_id: {e}")

    try:
        # Index para timestamp (Retención y ordenamiento)
        client.create_payload_index(
            collection_name="knowledge_base",
            field_name="timestamp",
            field_schema=models.PayloadSchemaType.DATETIME 
        )
        print("Index creado para 'timestamp' en knowledge_base.")
    except Exception as e:
        print(f"Nota sobre index timestamp: {e}")

if __name__ == "__main__":
    init_collections()
