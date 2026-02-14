import os
import asyncio
import sys
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from langchain_core.messages import HumanMessage
from app.graph.workflow import workflow
from app.core.checkpoint import get_postgres_checkpointer

# Fix para Windows
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    print("❌ Error: TELEGRAM_BOT_TOKEN no encontrado en .env")
    sys.exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde al comando /start"""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="👋 ¡Hola! Soy EMACE.\n\nPuedo ayudarte con facturación, soporte técnico y ventas. ¿En qué te ayudo hoy?"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa mensajes de texto con el Grafo"""
    user_text = update.message.text
    chat_id = str(update.effective_chat.id)
    
    # Notificar que está "escribiendo..."
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        # Usar Postgres Checkpointer para persistencia real por usuario (chat_id)
        async with get_postgres_checkpointer() as checkpointer:
            app = workflow.compile(checkpointer=checkpointer)
            
            config = {"configurable": {"thread_id": chat_id}}
            
            # Ejecutar grafo
            result = await app.ainvoke(
                {"messages": [HumanMessage(content=user_text)]},
                config
            )
            
            # Obtener respuesta final
            messages = result.get("messages", [])
            if not messages:
                response = "⚠️ No obtuve respuesta del sistema."
            else:
                response = messages[-1].content
                
            await context.bot.send_message(chat_id=chat_id, text=response)
            
    except Exception as e:
        error_msg = f"❌ Error interno: {str(e)}"
        print(error_msg)
        await context.bot.send_message(chat_id=chat_id, text="Lo siento, ocurrió un error procesando tu solicitud.")

def main():
    print("🤖 Iniciando Bot de Telegram...")
    application = ApplicationBuilder().token(TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    msg_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    
    application.add_handler(start_handler)
    application.add_handler(msg_handler)
    
    print("✅ Bot escuchando. Presiona Ctrl+C para detener.")
    application.run_polling()

if __name__ == '__main__':
    main()
