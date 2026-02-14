import sys
import os
# import pytest # Removing pytest dependency to run as script
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.api.main import app
from app.core.database.session import get_session
from app.core.database.models import User
from sqlmodel import Session, select, create_engine

# Mock engine for tests if needed, but we can use the real DB with a test user
# We will use the existing DB but rely on the seeded users

client = TestClient(app)

def test_chat_endpoint_user_context():
    print("\n--- 🕵️ Testing POST /chat with User Context ---")
    
    # 1. Send request with user_id = 1
    payload_u1 = {
        "message": "Hola, ¿qué productos tengo en mi inventario?",
        "thread_id": "test_thread_u1",
        "user_id": 1
    }
    
    # We mock the graph execution to verify config injection
    # OR we can let it run if the graph is connected to real tools.
    # Since we want to verify the API->Graph->Tool pipeline, let's try a real call
    # But the graph execution might be slow or require LLM.
    # Ideally we should mock the graph.ainvoke to check the 'config' passed to it.
    
    with patch("app.api.v1.endpoints.chat.graph.compile") as mock_compile:
        # Mock the app returned by compile
        mock_app = MagicMock()
        mock_compile.return_value = mock_app
        
        # Mock ainvoke to return a dummy response
        async def mock_ainvoke(input, config):
            # VERIFY HERE: Check if user_id is in config
            print(f"   -> Graph called with config: {config}")
            assert config["configurable"]["user_id"] == 1
            return {"messages": [MagicMock(content="Respuesta simulada", type="ai")]}
            
        mock_app.ainvoke = mock_ainvoke
        
        # Also mock get_postgres_checkpointer to avoid DB connection issues in this specific unit test context
        # or we can rely on the real one if env is set.
        # Let's try to mock it to isolate the API logic.
        with patch("app.api.v1.endpoints.chat.get_postgres_checkpointer") as mock_checkpointer:
             # Mock context manager
            mock_checkpointer.return_value.__aenter__.return_value = MagicMock()
            
            # Make request
            response = client.post("/api/v1/chat", json=payload_u1)
            
            assert response.status_code == 200
            print("✅ API accepted user_id=1")
            
            # Verify response structure
            data = response.json()
            assert data["response"] == "Respuesta simulada"

    # 2. Test with User 2
    payload_u2 = {
        "message": "Hola",
        "thread_id": "test_thread_u2",
        "user_id": 2
    }
    
    with patch("app.api.v1.endpoints.chat.graph.compile") as mock_compile:
        mock_app = MagicMock()
        mock_compile.return_value = mock_app
        
        async def mock_ainvoke(input, config):
            print(f"   -> Graph called with config: {config}")
            assert config["configurable"]["user_id"] == 2
            return {"messages": [MagicMock(content="Respuesta U2", type="ai")]}
            
        mock_app.ainvoke = mock_ainvoke
        
        with patch("app.api.v1.endpoints.chat.get_postgres_checkpointer") as mock_checkpointer:
            mock_checkpointer.return_value.__aenter__.return_value = MagicMock()
            response = client.post("/api/v1/chat", json=payload_u2)
            assert response.status_code == 200
            print("✅ API accepted user_id=2")

if __name__ == "__main__":
    test_chat_endpoint_user_context()
