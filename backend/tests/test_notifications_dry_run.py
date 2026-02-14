import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.tools.notifications import send_email_notification_tool
from langchain_core.runnables import RunnableConfig

def main():
    config = RunnableConfig(configurable={"user_id": 1})
    res = send_email_notification_tool.invoke(
        {"to": ["test@example.com"], "subject": "Prueba", "body": "Hola"},
        config=config,
    )
    print(res)

if __name__ == "__main__":
    main()
