# 🐋 Guía de Docker y Docker Compose (Arquitectura Optimizada)

Esta guía describe el flujo de trabajo profesional con Docker en EMACE, diseñado para máxima velocidad en WSL 2 y aislamiento total de dependencias.

---

## 🚀 Conceptos Clave del Nuevo Flujo

1. **Inmutabilidad en Build**: Las dependencias (Python y Node) se instalan durante la construcción de la imagen (`docker build`). No hay instalaciones en runtime al iniciar el contenedor.
2. **Sin venv en el Contenedor**: Docker ya proporciona el aislamiento necesario. No usamos entornos virtuales (`venv`) dentro de la imagen de Python, lo que reduce la complejidad y el tamaño.
3. **Volúmenes para Desarrollo**: Mapeamos el código local a `/app` en el contenedor para habilitar el **Hot Reload** (cambios instantáneos en el código sin reiniciar).
4. **pnpm en Docker**: El frontend utiliza `pnpm` dentro del contenedor para instalaciones ultra-rápidas y manejo eficiente de caché.

---

## 🛠️ Comandos Esenciales (WSL 2)

### 1. Iniciar el Entorno
Ejecuta esto desde tu terminal de WSL (Ubuntu):
```bash
docker compose up -d
```
*Nota: Ya NO se usa el comando `docker-compose` (con guion). Usa el plugin moderno `docker compose`.*

### 2. Reconstruir Imágenes (Critical)
Si agregas una nueva librería a `requirements.txt` o `package.json`, debes reconstruir las imágenes:
```bash
docker compose up -d --build
```

### 3. Ver Logs en Tiempo Real
```bash
docker compose logs -f backend
# o para el frontend:
docker compose logs -f frontend
```

### 4. Ejecutar Comandos dentro del Contenedor
```bash
# Ejemplo: Correr migraciones o scripts de carga
docker compose exec backend python seed_data.py all
```

---

## 📁 Configuración Técnica

### Backend (Dockerfile)
- **Base**: `python:3.11-slim`.
- **Flow**: Copia dependencias -> Instala via `pip` -> Copia código.
- **Optimización**: No hay `venv`. Todo se instala en el `site-packages` del sistema del contenedor.

### Frontend (Dockerfile)
- **Base**: `node:20-slim`.
- **Flow**: Instala `pnpm` -> Copia `package.json` -> `pnpm install` -> Copia código.
- **Rendimiento**: Utiliza el motor de Next.js optimizado para producción si es necesario, o modo dev con watchers.

### .dockerignore (OBLIGATORIO)
El archivo `.dockerignore` en la raíz es crítico para evitar que `node_modules` de Windows o archivos locales pesados se suban al contexto de build.

---

## ⚡ Optimizaciones en docker-compose.yml

El proyecto utiliza características modernas de Compose:
- **`mem_limit`**: Restricción de RAM por servicio para proteger tu host.
- **`restart: always`**: Asegura que los agentes se recuperen tras un error crítico.
- **Volumes**:
  - `./backend:/app`: Sincronización de código backend.
  - `./frontend:/app`: Sincronización de código frontend.
  - **Exclusión de node_modules**: `/app/node_modules` es un volumen anónimo para evitar conflictos entre el host y el contenedor.

---

## 🔴 Solución de Problemas (WSL)

### El Hot Reload no funciona
**Causa**: Estás trabajando en `/mnt/c/`.
**Solución**: Mueve el repo a `~/projects/emace` en la partición de Linux. Docker en Windows no puede enviar eventos de archivos de forma eficiente a través de montajes de red `/mnt/c`.

### Error de permisos en node_modules
**Causa**: Mezclaste comandos de Windows (`npm install`) con Docker.
**Solución**: Borra `node_modules` en tu host y deja que Docker lo maneje, o usa `pnpm install` **exclusivamente** dentro de WSL.
