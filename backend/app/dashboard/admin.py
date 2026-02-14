import streamlit as st
import asyncio
import sys

# Windows Check for AsyncIO
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import pandas as pd
from sqlmodel import Session, select
from app.core.database.session import engine
from app.core.database.models import User, Invoice, Product
from app.core.vector.client import client as qdrant
from app.graph.workflow import workflow as graph # Actualizado
from app.core.checkpoint import get_postgres_checkpointer
from langchain_core.messages import HumanMessage, AIMessage

st.set_page_config(page_title="Agent Admin Dashboard", layout="wide")

st.title("🤖 Ecosistema de Agentes - Panel de Control")

# Sidebar: Status
st.sidebar.header("Estado del Sistema")

# DB Status
try:
    with Session(engine) as session:
        user_count = session.exec(select(User)).all()
        st.sidebar.success(f"✅ PostgreSQL Conectado ({len(user_count)} usuarios)")
except Exception as e:
    st.sidebar.error(f"❌ PostgreSQL Error: {e}")

# Vector DB Status
try:
    cols = qdrant.get_collections().collections
    st.sidebar.success(f"✅ Qdrant Conectado ({len(cols)} colecciones)")
except Exception as e:
    st.sidebar.error(f"❌ Qdrant Error: {e}")

# Tabs
tab1, tab2, tab3 = st.tabs(["💬 Chat de Prueba", "📊 Datos SQL", "🧠 Memoria Vectorial"])

# --- TAB 1: CHAT ---
with tab1:
    st.header("Simulador de Chat")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    thread_id = st.text_input("Thread ID", "dashboard_test_1")
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
    if prompt := st.chat_input("Escribe tu mensaje..."):
        # User message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
            
        # Agent response logic
        async def run_agent():
            async with get_postgres_checkpointer() as checkpointer:
                app = graph.compile(checkpointer=checkpointer)
                config = {"configurable": {"thread_id": thread_id}}
                result = await app.ainvoke(
                    {"messages": [HumanMessage(content=prompt)]},
                    config
                )
                # Buscar el último mensaje que sea AIMessage (respuesta del agente) y no un SystemMessage de QA
                messages = result["messages"]
                response_text = "No response"
                
                for msg in reversed(messages):
                    if isinstance(msg, AIMessage) and msg.content:
                        response_text = msg.content
                        break
                    # Si encontramos el mensaje del usuario antes de una respuesta, es que no hubo respuesta
                    if isinstance(msg, HumanMessage):
                        break
                
                return response_text

        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                try:
                    response_text = asyncio.run(run_agent())
                    st.write(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                except Exception as e:
                    st.error(f"Error ejecutando el agente: {e}")

# --- TAB 2: DATA SQL ---
with tab2:
    st.header("Explorador de Base de Datos")
    
    table_option = st.selectbox("Selecciona Tabla", ["Users", "Invoices", "Products"])
    
    with Session(engine) as session:
        if table_option == "Users":
            data = session.exec(select(User)).all()
        elif table_option == "Invoices":
            data = session.exec(select(Invoice)).all()
        elif table_option == "Products":
            data = session.exec(select(Product)).all()
            
        if data:
            df = pd.DataFrame([d.model_dump() for d in data])
            st.dataframe(df)
        else:
            st.info("No hay datos en esta tabla.")

# --- TAB 3: VECTOR DB ---
with tab3:
    st.header("Memoria Vectorial (Qdrant)")
    
    if cols:
        col_name = st.selectbox("Colección", [c.name for c in cols])
        
        # Get Info
        info = qdrant.get_collection(col_name)
        st.write(f"**Puntos (Vectores):** {info.points_count}")
        st.write(f"**Estado:** {info.status}")
        
        # Scroll points
        points = qdrant.scroll(collection_name=col_name, limit=10)[0]
        if points:
            st.write("### Muestra de Datos (Payload)")
            for p in points:
                st.json(p.payload)
        else:
            st.info("Colección vacía.")
