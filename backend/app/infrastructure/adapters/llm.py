import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def get_llm(role: str = "supervisor", temperature: float = 0):
    """
    Retorna una instancia configurada de ChatOpenAI para OpenRouter,
    seleccionando el modelo adecuado según el rol del agente.
    """
    model_map = {
        "supervisor": os.getenv("MODEL_SUPERVISOR", "stepfun/step-3.5-flash:free"),
        "billing": os.getenv("MODEL_BILLING", "openrouter/aurora-alpha"),
        "tech": os.getenv("MODEL_TECH", "stepfun/step-3.5-flash:free"),
        "sales": os.getenv("MODEL_SALES", "openrouter/pony-alpha"),
        "qa": os.getenv("MODEL_QA", "stepfun/step-3.5-flash:free"),
        "rag": os.getenv("MODEL_RAG", "liquid/lfm-2.5-1.2b-thinking:free"),
        "default": os.getenv("MODEL_NAME", "stepfun/step-3.5-flash:free")
    }
    
    model_name = model_map.get(role.lower(), model_map["default"])
    print(f"DEBUG: [LLM Factory] Rol: '{role}' -> Modelo: '{model_name}'")

    return ChatOpenAI(
        model=model_name,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=temperature,
        # OpenRouter requiere headers específicos para ranking
        model_kwargs={
            "extra_headers": {
                "HTTP-Referer": "https://localhost:3000",
                "X-Title": "Trae Agent Framework"
            }
        }
    )
