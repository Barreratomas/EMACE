from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from app.interfaces.api.deps import get_current_user
from app.domain.models import User
from app.infrastructure.database.session import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.security import decode_token
from app.application.use_cases.chat_use_cases import ChatUseCases
from app.infrastructure.adapters.checkpoint import get_postgres_checkpointer
import json

router = APIRouter()
chat_use_cases = ChatUseCases()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        from starlette.websockets import WebSocketState
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default_thread"

class ChatResponse(BaseModel):
    response: str

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Punto de entrada para el chat directo con el agente orquestador (HTTP POST)"""
    async with get_postgres_checkpointer() as checkpointer:
        response = await chat_use_cases.process_chat_message(
            request.message, 
            request.thread_id, 
            current_user,
            checkpointer
        )
    return ChatResponse(response=response)

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_async_session)
):
    """Endpoint de comunicación en tiempo real mediante WebSockets para el chat"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                token = message_data.get("token")
                message = message_data.get("message")
                
                if not token or not message:
                    continue
                
                payload = decode_token(token)
                if not payload:
                    continue
                
                await manager.send_personal_message(f"Echo: {message}", websocket)
                
            except Exception:
                continue
    except WebSocketDisconnect:
        manager.disconnect(websocket)
