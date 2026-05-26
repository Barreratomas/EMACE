# Guía de Configuración WSL 2 (Entorno de Alto Rendimiento)

Esta guía explica cómo configurar el entorno de desarrollo optimizado para **EMACE**. Trabajar directamente en el sistema de archivos de Linux dentro de WSL 2 es **obligatorio** para garantizar el rendimiento, la estabilidad de Docker y el funcionamiento de los "watchers" de archivos.

---

## REGLA CRÍTICA DE SUPERVIVENCIA
**NUNCA** trabajes sobre `/mnt/c/` o carpetas sincronizadas con **OneDrive**.
- **PROHIBIDO**: `/mnt/c/Users/Nombre/Documents/emace`
- **CORRECTO**: `~/projects/emace` (dentro del sistema de archivos nativo de Linux)

**¿Por qué?**
1. **Rendimiento**: Acceder a archivos de Windows desde Linux es hasta 100 veces más lento.
2. **Watchers**: Next.js y FastAPI no detectarán cambios en los archivos (Hot Reload fallará).
3. **Docker**: Los volúmenes en `/mnt/c` causan errores de permisos y bloqueos de I/O.
4. **Node Modules**: `pnpm install` fallará o será extremadamente lento sobre sistemas de archivos Windows.

---

## 1. Instalación de WSL 2
Si aún no tienes WSL 2 instalado:
1. Abre PowerShell como Administrador.
2. Ejecuta:
   ```powershell
   wsl --install
   ```
3. Reinicia la PC. Se instalará **Ubuntu** por defecto. Crea tu usuario y contraseña de Linux.

---

## 2. Docker Desktop + Integración WSL
1. Instala [Docker Desktop para Windows](https://www.docker.com/products/docker-desktop/).
2. En la configuración de Docker Desktop:
   - **General**: Activa "Use the WSL 2 based engine".
   - **Resources > WSL Integration**: Activa el switch para tu distribución (ej: `Ubuntu`).

---

## 3. Mover el Proyecto a la Partición de Linux
Abre tu terminal de **Ubuntu** y ejecuta:
```bash
# Crear directorio de trabajo
mkdir -p ~/projects
cd ~/projects

# Clonar el repo (recomendado)
git clone <URL_DEL_REPO> emace
cd emace
```

### Apertura con VS Code
Para editar archivos de Linux con la interfaz de Windows:
1. Instala la extensión **WSL** en VS Code (ID: `ms-vscode-remote.remote-wsl`).
2. En la terminal de Ubuntu, dentro de la carpeta del proyecto, escribe:
   ```bash
   code .
   ```
VS Code se conectará al servidor dentro de Linux.

---

## 4. Instalación de Herramientas (SOLO LINUX)

### Python 3.11 (Sistema)
No uses el instalador de python.org. Usa los repositorios de Ubuntu:
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip -y
```

### Node.js y pnpm (Vía nvm)
Evita instalar Node en Windows. Instálalo dentro de WSL:
```bash
# 1. Instalar nvm (Node Version Manager)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# 2. Cargar nvm (o cierra y abre la terminal)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# 3. Instalar Node 20 (LTS)
nvm install 20
nvm use 20

# 4. Instalar pnpm (Gestor de paquetes ultra-rápido)
npm install -g pnpm
```

---

## 5. Checklist de Verificación
- [ ] Ejecuto `ls` y NO veo `/mnt/c/`.
- [ ] Mi terminal dice `user@ubuntu:~/projects/emace$`.
- [ ] VS Code muestra `WSL: Ubuntu` en la esquina inferior izquierda.
- [ ] `pnpm --version` funciona en la terminal de Linux.
- [ ] `python3 --version` devuelve 3.11.x.
