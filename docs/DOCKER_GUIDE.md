# Guía de Docker para el Proyecto Agent

Esta guía proporciona instrucciones detalladas sobre cómo gestionar el entorno de desarrollo utilizando Docker Compose en este proyecto.

## Requisitos Previos

- Docker Desktop instalado y configurado para usar **WSL 2 backend**.
- WSL 2 (Windows Subsystem for Linux) instalado en tu sistema Windows.

## Importante: Prefijo `wsl`

Debido a que el proyecto se ejecuta dentro de un entorno WSL, **todos los comandos de Docker deben ir precedidos por `wsl`** si los ejecutas desde una terminal de Windows (PowerShell o CMD).

Ejemplo:
```bash
wsl docker compose up -d
```
docker compose up postgres qdrant adminer cloudflared backend -d
---

## Comandos Comunes

### 1. Iniciar los Servicios
Inicia todos los contenedores en segundo plano:
```bash
wsl docker compose up -d
```

### 2. Ver Logs
Para ver qué está pasando en tiempo real (especialmente útil para el backend):
```bash
wsl docker compose logs -f backend
```

### 3. Detener los Servicios
Detiene los contenedores pero mantiene los volúmenes (base de datos intacta):
```bash
wsl docker compose stop
```

Para detener y eliminar los contenedores:
```bash
wsl docker compose down
```

### 4. Reconstruir Imágenes (Forzar actualización)
Si has hecho cambios en archivos de configuración como `docker-compose.yml` o necesitas forzar la reinstalación de dependencias:
```bash
wsl docker compose up -d --build
```

### 5. Reiniciar un Servicio Específico
Si el backend falla o necesitas reiniciarlo:
```bash
wsl docker compose restart backend
```

---

## Servicios Incluidos

| Servicio | Puerto | Descripción |
| :--- | :--- | :--- |
| `postgres` | `5433` | Base de datos relacional (PostgreSQL 15). |
| `qdrant` | `6333` | Base de datos vectorial para el conocimiento de los agentes. |
| `adminer` | `8081` | Interfaz web para gestionar la base de datos PostgreSQL. |
| `backend` | `8000` | API FastAPI (Python 3.11). |
| `frontend` | `3000` | Aplicación Next.js (Node 20). |
| `cloudflared` | - | Túnel de Cloudflare para acceso externo (si se configura). |

---

## Solución de Problemas Comunes

### Error: `ModuleNotFoundError`
Si ves un error indicando que falta una librería (ej: `telethon`), es posible que el entorno virtual dentro del contenedor no se haya actualizado. 

**Solución:**
Reinicia el contenedor del backend. La configuración actual de `docker-compose.yml` está diseñada para intentar instalar las dependencias de `requirements-docker.txt` cada vez que el servicio se inicia.
```bash
wsl docker compose restart backend
```

### Limpiar Volúmenes
Si necesitas empezar de cero con la base de datos (¡Cuidado: esto borra todos los datos!):
```bash
wsl docker compose down -v
```

---

## Integración con Telegram y Túneles (Cloudflare)

El sistema está configurado para manejar automáticamente las URLs cambiantes de los túneles (como Cloudflare Tunnel).

### 1. Detección de URL Pública
Para que el bot de Telegram y los webhooks de Mercado Pago funcionen, el sistema necesita saber su URL pública.
- El backend intenta detectar esta URL automáticamente a partir de la variable `MP_WEBHOOK_URL` en el archivo `.env`.
- Si `MP_WEBHOOK_URL` es `https://mi-tunel.trycloudflare.com/api/v1/billing/webhook/mp`, el sistema asumirá que la base pública es `https://mi-tunel.trycloudflare.com`.

### 2. Sincronización Automática
Cada vez que el backend se inicia (`wsl docker compose restart backend`), el sistema:
1. Lee todas las integraciones de Telegram activas en la base de datos.
2. Registra automáticamente el webhook en los servidores de Telegram usando la URL del túnel actual.
3. Esto elimina la necesidad de reconfigurar manualmente el bot cada vez que reinicias el túnel.

### 3. Configuración Manual (Opcional)
Si deseas forzar una URL específica, puedes definirla en el `.env` del backend:
```env
TELEGRAM_PUBLIC_BASE_URL=https://tu-dominio-personal.com
```

---

## Estructura de Archivos
- `docker-compose.yml`: Configuración principal de la orquestación.
- `backend/requirements-docker.txt`: Dependencias específicas para el entorno Docker.
- `backend/.env`: Variables de entorno para el backend.
- `frontend/.env.local`: Variables de entorno para el frontend.
