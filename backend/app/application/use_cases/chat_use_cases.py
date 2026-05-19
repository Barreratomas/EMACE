import json
from fastapi import HTTPException
from langchain_core.messages import HumanMessage, AIMessage
from app.application.graph.workflow import builder
from app.domain.models import User
from typing import Any

class ChatUseCases:
    async def process_chat_message(
        self, 
        message: str, 
        thread_id: str, 
        current_user: User,
        checkpointer: Any
    ) -> str:
        try:
            config = {
                "configurable": {
                    "thread_id": thread_id, 
                    "user_id": current_user.id
                }
            }
            
            user_info = {
                "id": current_user.id,
                "name": current_user.name,
                "role": current_user.role.name if current_user.role else "vendor",
                "permissions": current_user.role.permissions if current_user.role else []
            }
            
            # Compilamos el grafo usando el checkpointer inyectado desde infraestructura
            app = builder.compile(checkpointer=checkpointer)
            
            result = await app.ainvoke(
                {
                    "messages": [HumanMessage(content=message)],
                    "user_info": user_info
                },
                config
            )
            
            if result and "messages" in result:
                last_message = result["messages"][-1]
                if isinstance(last_message, AIMessage):
                    return str(last_message.content)
            
            return "El sistema no pudo generar una respuesta."
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
