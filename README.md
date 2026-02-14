# 🤖 EMACE (Ecosistema Multi-Agente Cognitivo Enterprise)

Este repositorio contiene **EMACE**, un sistema multi-agente avanzado capaz de realizar tareas complejas (facturación, soporte técnico, ventas) utilizando una arquitectura **Hub & Spoke** (Supervisor + Especialistas).

## 🌟 Características

- **Orquestación Inteligente**: Agente Supervisor (Router) que delega tareas.
- **Herramientas Reales**: Conexión a Base de Datos SQL (PostgreSQL) y Vectorial (Qdrant).
- **Memoria Persistente**: Historial de chat persistente y "Lecciones Aprendidas" (RAG).
- **Auto-Corrección (Fase 5)**: Ciclo QA -> Feedback -> Reintento.
- **API Profesional (Fase 6)**: Endpoints REST con FastAPI.
- **Dashboard de Administración**: Interfaz Streamlit para monitoreo y pruebas.

## 🛠️ Requisitos

- Python 3.10+
- Docker & Docker Compose
- Clave de API de OpenRouter (en `.env`)

## 🚀 Instalación

1.  **Clonar y configurar entorno**:
    ```bash
    python -m venv venv
    venv\Scripts\activate
    
    cd backend
    pip install -r requirements.txt
    ```

2.  **Configurar Variables de Entorno**:
    Crea un archivo `.env` en la carpeta `backend` (ver `.env.example` o usar el existente) con:
    ```
    OPENROUTER_API_KEY=sk-...
    DATABASE_URL=postgresql://admin:SecurePass123!@localhost:5433/agent_db
    QDRANT_URL=http://localhost:6333
    ```

3.  **Levantar Infraestructura**:
    Desde la raíz del proyecto:
    ```bash
    docker-compose up -d
    ```

4.  **Inicializar Datos**:
    ```bash
    cd backend
    
    # Migraciones SQL
    alembic upgrade head
    
    # Inicializar Qdrant
    python app/core/vector/client.py
    
    # Poblar Datos de Prueba
    python seed_data.py
    ```

## 🏃‍♂️ Ejecución

### API REST
Inicia el servidor backend:
```bash
uvicorn app.api.main:app --reload
```
Documentación interactiva disponible en: `http://localhost:8000/docs`

### Dashboard de Administración
Interfaz gráfica para probar el chat y ver datos:
```bash
streamlit run app/dashboard/admin.py
```

## 🧪 Tests

- **Test Básico**: `python test_supervisor.py`
- **Test Auto-Corrección**: `python verify_fase5.py`
- **Test API**: `python verify_fase6_api.py`
