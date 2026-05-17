from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from app.graph.workflow import builder, workflow as graph
from app.core.checkpoint import get_postgres_checkpointer
from app.api.deps import get_current_user
from app.core.database.models import User, ChatHistory
from app.core.database.session import get_async_session
from app.core.memory.episodic import episodic_memory
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_token
import os
import json

router = APIRouter()

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
        # Usamos starlette.websockets.WebSocketState que es de donde FastAPI lo hereda
        from starlette.websockets import WebSocketState
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_text(message)
        else:
            print(f"⚠️ Intento de enviar mensaje a WebSocket cerrado/desconectado.")

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
    try:
        # Process message with LangGraph and Persistence
        config = {"configurable": {"thread_id": request.thread_id, "user_id": current_user.id}}
        
        # User metadata for the graph state
        user_info = {
            "id": current_user.id,
            "name": current_user.name,
            "role": current_user.role.name if current_user.role else "vendor",
            "permissions": current_user.role.permissions if current_user.role else []
        }
        
        async with get_postgres_checkpointer() as checkpointer:
            app = builder.compile(checkpointer=checkpointer)
            result = await app.ainvoke(
                {
                    "messages": [HumanMessage(content=request.message)],
                    "user_info": user_info
                },
                config
            )
        
        if result and "messages" in result:
            last_message = result["messages"][-1]
            if isinstance(last_message, AIMessage):
                return ChatResponse(response=last_message.content)
        
        return ChatResponse(response="El sistema no pudo generar una respuesta.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_async_session)
):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                token = message_data.get("token")
                message = message_data.get("message")
                thread_id = message_data.get("thread_id", "default_thread")

                if not token:
                    await manager.send_personal_message(json.dumps({"error": "No token provided"}), websocket)
                    continue
                
                try:
                    payload = decode_token(token)
                    user_id = payload.get("sub")
                except Exception:
                    await manager.send_personal_message(json.dumps({"error": "Invalid token"}), websocket)
                    continue

                if not message:
                    continue

                # Process message with LangGraph and Persistence
                config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}
                
                # Fetch user for metadata (Websocket context)
                from app.core.database.models import User
                from sqlalchemy.future import select
                from sqlalchemy.orm import selectinload
                
                # Usamos la sesión inyectada por Depends
                query = select(User).where(User.id == int(user_id)).options(selectinload(User.role))
                result = await db.execute(query)
                db_user = result.scalars().first()
                
                if not db_user:
                    await manager.send_personal_message(json.dumps({"error": "User not found"}), websocket)
                    continue

                user_info = {
                    "id": db_user.id,
                    "name": db_user.name,
                    "role": db_user.role.name if db_user.role else "vendor",
                    "permissions": db_user.role.permissions if db_user.role else []
                }

                # Streaming response with checkpointer
                async with get_postgres_checkpointer() as checkpointer:
                    app = builder.compile(checkpointer=checkpointer)
                    async for event in app.astream(
                        {
                            "messages": [HumanMessage(content=message)],
                            "user_info": user_info
                        },
                        config,
                        stream_mode="updates"
                    ):
                        # En modo 'updates', event es un dict: { "NodeName": { "messages": [...], "next": "..." } }
                        for node_name, output in event.items():
                            if "messages" in output:
                                for msg in output["messages"]:
                                    # Solo enviamos AIMessages que no sean internos.
                                    # Los mensajes internos suelen empezar con '[' (QA feedback) 
                                    # o ser SystemMessages de notificación (QA Approved).
                                    if isinstance(msg, AIMessage) and msg.content:
                                        content = str(msg.content)
                                        # Filtramos feedback de QA, notificaciones técnicas y prompts de ruteo
                                        is_internal = (
                                            content.startswith("[") or 
                                            "QA Notification" in content or
                                            "Basado en la conversación anterior" in content
                                        )
                                        
                                        if not is_internal:
                                            await manager.send_personal_message(
                                                json.dumps({
                                                    "type": "message",
                                                    "content": content,
                                                    "thread_id": thread_id,
                                                    "node": node_name
                                                }), 
                                                websocket
                                            )

            except json.JSONDecodeError:
                await manager.send_personal_message(json.dumps({"error": "Invalid JSON"}), websocket)
            except Exception as e:
                await manager.send_personal_message(json.dumps({"error": str(e)}), websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)
