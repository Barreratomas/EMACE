# EMACE: Ecosistema Multi-Agente Cognitivo Enterprise

EMACE es una plataforma avanzada de asistencia inteligente **proactiva** y **Multi-Tenant**, diseñada para resolver consultas complejas y ejecutar acciones empresariales (Facturación, Soporte, Ventas e Inventario) utilizando una arquitectura **Hub-and-Spoke** con agentes especializados coordinados por un Supervisor central.

---

## REGLA CRÍTICA DE DESARROLLO (WSL 2)
Para un rendimiento óptimo y estabilidad de Docker/Next.js, este proyecto **DEBE** residir en el sistema de archivos nativo de Linux.
- **NUNCA** uses `/mnt/c/` o carpetas sincronizadas con **OneDrive**.
- **SIEMPRE** usa `~/projects/emace` o similar dentro de tu distribución de WSL (ej. Ubuntu).

Consulta la [Guía de Configuración WSL 2](docs/WSL_SETUP.md) para preparar tu entorno.

---

## Inicio Rápido con Docker

El flujo principal de desarrollo está 100% dockerizado. Las dependencias se instalan durante el build, garantizando consistencia.

### 1. Preparar el Entorno
```bash
# Entrar al directorio del proyecto en WSL
cd ~/projects/emace

# Configurar variables de entorno
cp backend/.env.example backend/.env
# Edita backend/.env con tus API Keys (OpenRouter, etc.)
```

### 2. Levantar el Ecosistema
```bash
docker compose up -d
```
Esto iniciará:
- **Backend (FastAPI)**: http://localhost:8000
- **Frontend (Next.js + pnpm)**: http://localhost:3000
- **Base de Datos (PostgreSQL)**
- **Memoria Vectorial (Qdrant)**

Consulta la [Guía de Docker](docs/DOCKER_GUIDE.md) para comandos avanzados (logs, builds, etc.).

---

## Stack Tecnológico

- **Core Cognitivo**: Python 3.11 + LangGraph + LangChain.
- **API**: FastAPI (Asíncrono, Type-Safe).
- **Frontend**: Next.js 15 (App Router) + Tailwind CSS v4 + **pnpm**.
- **Bases de Datos**: 
  - **SQL**: PostgreSQL (SQLModel).
  - **Vector**: Qdrant (RAG & Memoria Episódica).
- **Infraestructura**: Docker Compose V2 (con límites de memoria y reinicio automático).

---

## Estructura del Proyecto (Arquitectura Hexagonal)

El backend sigue el patrón **Ports & Adapters**, desacoplando la lógica de negocio de la infraestructura técnica.

- `/backend/app`:
  - `domain/`: **Núcleo de Negocio**. Contiene modelos (SQLModel), esquemas (Pydantic), prompts y definiciones de Puertos (interfaces abstractas). *No tiene dependencias externas.*
  - `application/`: **Casos de Uso**. Orquesta la lógica de negocio y flujos de trabajo (LangGraph). Depende solo del Dominio.
  - `infrastructure/`: **Adaptadores de Salida**. Implementaciones concretas de persistencia (Repositories), clientes de APIs externas (LLM, Telegram), configuración y seguridad.
  - `interfaces/`: **Adaptadores de Entrada**. Puntos de acceso externos como la API REST (FastAPI) y el Dashboard administrativo.
- `/frontend`: Dashboard industrial moderno (Next.js 15 + Tailwind CSS v4).
- `/docs`: Documentación técnica y funcional detallada.

---

## Desarrollo Local (Manual)

Si necesitas ejecutar servicios fuera de Docker para debugging profundo:

### Backend (Linux/WSL)
```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# El servidor inicia desde el adaptador de entrada de la API
uvicorn app.interfaces.api.main:app --reload
```

### Frontend (Linux/WSL)
```bash
cd frontend
pnpm install
pnpm dev
```

---

## Documentación Adicional
- [Arquitectura del Sistema](docs/DISEÑO_DEL_SISTEMA.md)
- [Guía de Usuario](docs/GUIA_USUARIO.md)
- [Setup de WSL 2](docs/WSL_SETUP.md)
- [Guía de Docker Avanzada](docs/DOCKER_GUIDE.md)
