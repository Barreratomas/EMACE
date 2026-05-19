from typing import List
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from sqlmodel import Session
from app.infrastructure.database.session import engine
from app.infrastructure.adapters.comm.notifications import send_email_notification

@tool
def send_email_notification_tool(
    to: List[str],
    subject: str,
    body: str,
    config: RunnableConfig
) -> str:
    """
    Envía un correo electrónico usando la configuración del sistema y registra auditoría.
    """
    user_id = config.get("configurable", {}).get("user_id")
    if not user_id:
        return "Error de Seguridad: No se identificó al usuario."
    with Session(engine) as session:
        return send_email_notification(session, user_id, to, subject, body)
