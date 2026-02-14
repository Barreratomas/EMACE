import logging
from typing import Optional, Dict, Any
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from app.core.config import get_settings
from app.core.database.session import get_async_session
from app.core.database.models import Customer, User
from sqlmodel import select
from app.graph.workflow import workflow as graph
from langchain_core.messages import HumanMessage, AIMessage
from app.core.checkpoint import get_postgres_checkpointer

settings = get_settings()
logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.application = None
        if self.token:
            self.application = ApplicationBuilder().token(self.token).build()
            self._setup_handlers()

    def _setup_handlers(self):
        """Configura los manejadores de comandos y mensajes."""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /start."""
        chat_id = str(update.effective_chat.id)
        welcome_text = (
            "👋 ¡Hola! Bienvenido al asistente inteligente de tu tienda.\n\n"
            "Para comenzar, por favor identifícate o solicita ayuda."
        )
        await update.message.reply_text(welcome_text)
        logger.info(f"Telegram user started: {chat_id}")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa los mensajes de texto recibidos ruteándolos al agente."""
        chat_id = str(update.effective_chat.id)
        user_text = update.message.text
        
        # 1. Identificar al Customer por telegram_chat_id
        customer = await self._get_customer_by_chat_id(chat_id)
        
        if not customer:
            await update.message.reply_text(
                "❌ No estás registrado en nuestro sistema. "
                "Por favor, contacta con el administrador de la tienda para vincular tu cuenta de Telegram."
            )
            return

        # 2. Obtener el contexto del Vendedor (User) dueño de este cliente
        vendor = await self._get_vendor_by_id(customer.user_id)
        if not vendor:
            await update.message.reply_text("Error interno: No se encontró al vendedor asociado.")
            return

        # 3. Enviar al Grafo de Agentes (LangGraph)
        try:
            response_text = await self._process_with_agent(
                message=user_text,
                chat_id=chat_id,
                customer=customer,
                vendor=vendor
            )
            await update.message.reply_text(response_text)
        except Exception as e:
            logger.error(f"Error processing agent message: {e}")
            await update.message.reply_text("Lo siento, tuve un problema procesando tu solicitud.")

    async def _get_customer_by_chat_id(self, chat_id: str) -> Optional[Customer]:
        """Busca un cliente por su ID de Telegram."""
        async for session in get_async_session():
            statement = select(Customer).where(Customer.telegram_chat_id == chat_id)
            result = await session.execute(statement)
            return result.scalar_one_or_none()
        return None

    async def _get_vendor_by_id(self, vendor_id: int) -> Optional[User]:
        """Busca al vendedor por su ID."""
        async for session in get_async_session():
            statement = select(User).where(User.id == vendor_id)
            result = await session.execute(statement)
            return result.scalar_one_or_none()
        return None

    async def _process_with_agent(self, message: str, chat_id: str, customer: Customer, vendor: User) -> str:
        """Invoca el grafo de agentes con el contexto del cliente."""
        async with get_postgres_checkpointer() as checkpointer:
            app = graph.compile(checkpointer=checkpointer)
            
            # Contexto de ejecución
            config = {
                "configurable": {
                    "thread_id": f"telegram_{chat_id}",
                    "user_id": vendor.id, # Contexto del tenant (Vendedor)
                    "customer_id": customer.id, # Identidad del cliente final
                    "channel": "telegram",
                    "user_role": "customer", # Rol limitado
                    "user_permissions": ["customer:access"] # Permisos mínimos
                }
            }
            
            result = await app.ainvoke(
                {"messages": [HumanMessage(content=message)]},
                config
            )
            
            # Extraer respuesta
            messages = result.get("messages", [])
            for m in reversed(messages):
                if isinstance(m, AIMessage) and m.content:
                    # Evitar notificaciones internas de QA en la respuesta al cliente
                    if "QA Notification" not in str(m.content):
                        return str(m.content)
            
            return "He recibido tu mensaje, pero no pude generar una respuesta clara."

    async def start(self):
        """Inicia el bot en modo polling (para desarrollo)."""
        if self.application:
            logger.info("Starting Telegram Bot (Polling)...")
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
        else:
            logger.warning("Telegram Bot Token not configured.")

    async def stop(self):
        """Detiene el bot."""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()

    async def send_message(self, chat_id: str, text: str):
        """Envía un mensaje proactivo a un chat_id."""
        if self.application:
            await self.application.bot.send_message(chat_id=chat_id, text=text)

# Instancia global
telegram_service = TelegramService()
