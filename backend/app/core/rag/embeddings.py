from langchain_huggingface import HuggingFaceEmbeddings

# Modelo pequeño, rápido y efectivo para RAG local
# "all-MiniLM-L6-v2" es el estándar de facto para CPU/Local.
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_embeddings_instance = None

def get_embeddings():
    """
    Singleton para cargar el modelo de embeddings solo una vez.
    """
    global _embeddings_instance
    if _embeddings_instance is None:
        print(f"🔄 Cargando modelo de embeddings local: {MODEL_NAME}...")
        _embeddings_instance = HuggingFaceEmbeddings(model_name=MODEL_NAME)
        print("✅ Modelo de embeddings cargado.")
    return _embeddings_instance
