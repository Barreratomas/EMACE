# 📘 Guía de Usuario: EMACE (Agente AI Enterprise)

Bienvenido a **EMACE**. Esta guía te ayudará a configurar y poner en marcha tu propio asistente de inteligencia artificial para tu empresa, capaz de manejar ventas, soporte técnico y facturación.

---

## 1. Preparación del Entorno (OBLIGATORIO: WSL 2)

Para que el sistema funcione correctamente y con alta velocidad, **EMACE** requiere un entorno basado en Linux (WSL 2).

1.  **Sigue la [Guía de Configuración WSL 2](WSL_SETUP.md)**: Aquí aprenderás a instalar Docker Desktop, activar la integración con Linux y preparar tus herramientas (Python 3.11 y Node/pnpm dentro de Linux).
2.  **Ubicación Crítica**: Asegúrate de que el proyecto esté en `~/projects/emace` (dentro de Linux). **NO lo uses en carpetas de Windows como Escritorio, Documentos o OneDrive (/mnt/c/).**
3.  **Herramientas**: No instales Python o Node desde instaladores `.exe` de Windows. Usa los comandos de Linux detallados en la guía de setup.

---

## 2. Configuración de las "Llaves" (.env)

El sistema necesita credenciales para interactuar con los modelos de lenguaje y servicios externos.

1.  Abre tu terminal de WSL y entra a la carpeta del proyecto:
    ```bash
    cd ~/projects/emace
    ```
2.  Configura el backend:
    ```bash
    cp backend/.env.example backend/.env
    ```
3.  Edita el archivo `backend/.env` (recomendado usar VS Code con la extensión WSL) y reemplaza:
    - `OPENROUTER_API_KEY`: Tu clave de IA (ej: de OpenRouter).
    - `TELEGRAM_BOT_TOKEN`: El token de tu bot creado con @BotFather.

---

## 3. Cargar tus Datos (Clientes, Productos, Documentos)

El cerebro del agente se alimenta de la información que tú le proporciones.

### 📊 Datos de Negocio
Puedes cargar datos masivos utilizando scripts de carga. El sistema espera archivos en formatos compatibles (CSV/JSON) o vía API.

### 📚 Base de Conocimiento (PDF, MD, TXT)
El agente utiliza **RAG (Retrieval Augmented Generation)**. Puedes subir documentos que el agente consultará antes de responder.
- Los documentos se procesan y se guardan en la base de datos vectorial **Qdrant**.

### 📥 Procesar los datos iniciales
Desde la terminal de WSL:
```bash
docker compose exec backend python seed_data.py all
```

---

## 4. Encender el Sistema

Todo el ecosistema se inicia con un solo comando:

```bash
docker compose up -d
```

Esto encenderá automáticamente:
- **Base de Datos SQL** (PostgreSQL).
- **Base de Datos Vectorial** (Qdrant).
- **El Cerebro (Backend)**: FastAPI + Agentes de LangGraph.
- **El Panel de Control (Frontend)**: Dashboard en Next.js.

---

## 5. Usar el Panel de Control (Dashboard)

El Dashboard es tu centro de mando industrial.

1.  Abre tu navegador y ve a: [http://localhost:3000](http://localhost:3000)
2.  **Funcionalidades**:
    - Gestión de Inventario y Productos.
    - Configuración de Agentes y Bot de Telegram.
    - Monitoreo de actividad y logs.

---

## 6. Preguntas Frecuentes (FAQ)

*   **¿Cómo veo los logs del sistema?**: Ejecuta `docker compose logs -f`.
*   **Hice un cambio en el código y no se ve**: Next.js y FastAPI tienen **Hot Reload**, pero si cambiaste dependencias, ejecuta `docker compose up -d --build`.
*   **Error "Connection Refused"**: Asegúrate de que Docker Desktop esté corriendo y que la integración con WSL esté activa.
*   **¿Puedo usar npm?**: No, el proyecto está migrado a **pnpm** por rendimiento. Usa `pnpm install` si trabajas localmente.

---

## 7. Soporte y Mantenimiento

- **Actualizaciones**: Siempre realiza un `git pull` y luego `docker compose up -d --build`.
- **Limpieza**: Para borrar datos y empezar de cero, usa `docker compose down -v`.
