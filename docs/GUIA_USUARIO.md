
# 📘 Guía de Usuario: EMACE (Agente AI Enterprise)

Bienvenido a **EMACE**. Esta guía te ayudará a configurar y poner en marcha tu propio asistente de inteligencia artificial para tu empresa, capaz de manejar ventas, soporte técnico y facturación.

No necesitas ser un experto en programación para usarlo, solo sigue estos pasos.

---

## 1. Preparación del Entorno (Lo que necesitas instalar)

Antes de empezar, asegúrate de tener instalados estos dos programas en tu computadora:

1.  **Docker Desktop**: Es el "motor" donde viven las bases de datos.
    *   Descárgalo aquí: [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
    *   Instálalo y ábrelo (debe quedar corriendo en segundo plano).
2.  **Python**: El lenguaje en el que habla el agente.
    *   Descárgalo aquí: [https://www.python.org/downloads/](https://www.python.org/downloads/)
    *   ⚠️ **Importante**: Al instalar, marca la casilla **"Add Python to PATH"**.

---

## 2. Configuración de las "Llaves" (.env)

El sistema necesita contraseñas y claves para funcionar (como la llave de tu casa).

1.  Entra a la carpeta `backend` dentro del proyecto.
2.  Busca un archivo llamado `.env` (si no existe, crea uno nuevo).
3.  Ábrelo con el Bloc de Notas.
4.  Copia y pega el siguiente contenido, reemplazando los valores donde dice `tu_...`:

```ini
# --- LLAVES DE INTELIGENCIA ARTIFICIAL ---
# Consigue tu clave gratis/paga en: https://openrouter.ai/keys
OPENROUTER_API_KEY=sk-or-v1-tu-clave-aqui...

# --- TELEGRAM ---
# Consigue tu token hablando con @BotFather en Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-tu-token-aqui...

# --- CONFIGURACIÓN TÉCNICA (NO TOCAR) ---
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
MODEL_NAME=stepfun/step-3.5-flash:free
MODEL_SUPERVISOR=stepfun/step-3.5-flash:free
MODEL_BILLING=openrouter/aurora-alpha
MODEL_TECH=stepfun/step-3.5-flash:free
MODEL_SALES=openrouter/pony-alpha
MODEL_QA=stepfun/step-3.5-flash:free
MODEL_RAG=liquid/lfm-2.5-1.2b-thinking:free
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
DATABASE_URL=postgresql://admin:SecurePass123!@localhost:5433/agent_db
Qdrant_URL=http://localhost:6333
```

---

## 3. Cargar tus Datos (Clientes, Productos, Documentos)

Para que el agente sepa sobre TU empresa, debes darle información.

1.  Ve a la carpeta `backend` y busca (o crea) la carpeta `data/inputs` (quedaría: `backend/data/inputs`).
2.  Coloca ahí tus archivos:

### 📊 Datos de Negocio (Excel/CSV)
Crea estos archivos en Excel y guárdalos como **CSV (delimitado por comas)**:

*   **`users.csv`**: Tus clientes.
    *   Columnas: `name,email,plan_type`
    *   Ejemplo: `Juan Perez,juan@email.com,premium`
*   **`products.csv`**: Tu catálogo.
    *   Columnas: `name,category,price,stock,description`
    *   Ejemplo: `Servidor Dell,Hardware,2000,10,Servidor potente`
*   **`invoices.csv`**: Facturas pendientes/pagadas.
    *   Columnas: `client_email,amount,status,due_date`
    *   Ejemplo: `juan@email.com,500.00,pending,2024-12-01`

### 📚 Documentos (PDF, Texto)
Simplemente arrastra tus manuales, guías o políticas de empresa a la misma carpeta `data/inputs`.
*   Formatos aceptados: `.pdf`, `.txt`, `.md`.
*   El agente leerá todo esto para responder preguntas técnicas o de procesos.

### 📥 Procesar los datos
Una vez guardados los archivos, abre una terminal (PowerShell o CMD) en la carpeta del proyecto y ejecuta:

```bash
# Entrar a la carpeta del backend
cd backend

# Cargar TODO (Bases de datos y Documentos)
python seed_data.py all
```

Verás mensajes verdes ✅ confirmando que la información fue cargada.

---

## 4. Encender el Sistema

### Paso 1: Iniciar las Bases de Datos
Asegúrate de que Docker esté abierto y ejecuta en la terminal:

```bash
docker-compose up -d
```
*(Solo necesitas hacer esto una vez o cuando reinicies la PC)*.

### Paso 2: Activar el Cerebro (Bot de Telegram)
Para que el agente empiece a escuchar en Telegram, ejecuta:

```bash
python app/channels/telegram_bot.py
```

Si ves el mensaje:
> `✅ Bot escuchando. Presiona Ctrl+C para detener.`

¡Felicidades! 🎉 Ve a Telegram, busca tu bot y empieza a chatear.

---

## 5. Usar el Panel de Control (Dashboard)
El sistema incluye una interfaz visual moderna para gestionar el inventario y ver métricas.

### Requisitos Previos
Necesitas tener **Node.js** instalado (v18 o superior). Descárgalo en [nodejs.org](https://nodejs.org/).

### Pasos
1.  Abre una **NUEVA** terminal (no cierres la del sistema principal).
2.  Entra a la carpeta del frontend:
    ```bash
    cd frontend
    ```
3.  Instala las dependencias (solo la primera vez):
    ```bash
    npm install
    ```
4.  Inicia el panel visual:
    ```bash
    npm run dev
    ```
5.  Abre tu navegador web y ve a: [http://localhost:3000](http://localhost:3000)

Aquí podrás:
- Ver tu inventario en tiempo real.
- Agregar nuevos productos o servicios.
- Editar precios y stock.
- Pausar ventas de productos específicos.

---

## 6. Preguntas Frecuentes (FAQ)

*   **Error "ModuleNotFoundError"**: Te falta instalar librerías. Ejecuta: `pip install -r requirements.txt`
*   **El bot no responde**: Revisa que tu `TELEGRAM_BOT_TOKEN` en el archivo `.env` sea correcto.
*   **Docker no conecta**: Asegúrate de que la aplicación Docker Desktop esté abierta y con las luces en verde.
