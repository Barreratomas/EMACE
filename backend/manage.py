import os
import sys
import subprocess
import argparse
from pathlib import Path

# Rutas
# Este script vive en agent/backend, por lo que BASE_DIR es .../agent/backend
BASE_DIR = Path(__file__).parent.absolute()

def run_command(command, cwd=None, env=None):
    """Ejecuta un comando de consola con la configuración de entorno adecuada."""
    if cwd is None:
        cwd = BASE_DIR
        
    # Preparar variables de entorno
    cmd_env = os.environ.copy()
    if env:
        cmd_env.update(env)
    
    # Asegurar que el directorio actual (backend) esté en PYTHONPATH para que funcionen las importaciones de 'app'
    current_pythonpath = cmd_env.get("PYTHONPATH", "")
    backend_str = str(BASE_DIR)
    if backend_str not in current_pythonpath:
        cmd_env["PYTHONPATH"] = f"{backend_str}{os.pathsep}{current_pythonpath}" if current_pythonpath else backend_str

    print(f"📂 Directorio de Trabajo: {cwd}")
    print(f"🚀 Ejecutando: {command}")
    print("-" * 40)
    
    try:
        subprocess.run(command, cwd=cwd, shell=True, check=True, env=cmd_env)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando el comando. Código de salida: {e.returncode}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n🛑 Detenido por el usuario.")

def start_api(args):
    """Inicia el servidor backend de FastAPI."""
    run_command("uvicorn app.api.main:app --reload")

def start_dashboard(args):
    """Inicia el Panel de Administración (Streamlit)."""
    run_command("streamlit run app/dashboard/admin.py")

def run_migrate(args):
    """Ejecuta las migraciones de la base de datos para actualizar a la última versión (head)."""
    run_command("alembic upgrade head")

def makemigrations(args):
    """Genera un nuevo script de migración basado en los cambios de los modelos."""
    message = args.message if args.message else "Migración generada automáticamente"
    run_command(f'alembic revision --autogenerate -m "{message}"')

def migrate_down(args):
    """Revierte la última migración aplicada (rollback)."""
    run_command("alembic downgrade -1")

def migrate_status(args):
    """Muestra el historial de migraciones y la revisión actual de la base de datos."""
    print("📜 Historial de Migraciones:")
    run_command("alembic history --verbose")
    print("\n📍 Revisión Actual:")
    run_command("alembic current")

def run_seed(args):
    """Carga la base de datos con datos iniciales de prueba."""
    run_command("python seed_data.py all")

def start_scheduler(args):
    """Inicia el planificador de tareas en segundo plano para trabajos proactivos."""
    run_command("python -c \"from app.core.scheduler import run_scheduler; run_scheduler()\"")

def run_test(args):
    """Ejecuta las pruebas de verificación de la API."""
    run_command("python tests/verify_fase6_api.py")

def install_deps(args):
    """Instala las dependencias del backend."""
    run_command("pip install -r requirements.txt")

def main():
    parser = argparse.ArgumentParser(
        description="Script de Gestión de Agentes EMACE (Backend)",
        epilog="Ejemplo: python manage.py api"
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # Registro de comandos
    subparsers.add_parser("api", help="Iniciar backend FastAPI (uvicorn)")
    subparsers.add_parser("dashboard", help="Iniciar Panel de Administración (streamlit)")
    
    # Migraciones (Alembic)
    subparsers.add_parser("migrate", help="Aplicar migraciones pendientes a la base de datos")
    
    make_parser = subparsers.add_parser("makemigrations", help="Crear nueva migración desde cambios en modelos")
    make_parser.add_argument("-m", "--message", help="Mensaje/descripción de la migración", type=str)
    
    subparsers.add_parser("migrate-down", help="Revertir la última migración aplicada")
    subparsers.add_parser("migrate-status", help="Mostrar historial y versión actual de migraciones")
    
    subparsers.add_parser("seed", help="Cargar base de datos con datos de prueba")
    subparsers.add_parser("scheduler", help="Iniciar planificador de tareas en segundo plano")
    subparsers.add_parser("test", help="Ejecutar pruebas de verificación de API")
    subparsers.add_parser("install", help="Instalar dependencias de requirements.txt")

    args = parser.parse_args()

    # Mapeo de comandos
    commands = {
        "api": start_api,
        "dashboard": start_dashboard,
        "migrate": run_migrate,
        "makemigrations": makemigrations,
        "migrate-down": migrate_down,
        "migrate-status": migrate_status,
        "seed": run_seed,
        "scheduler": start_scheduler,
        "test": run_test,
        "install": install_deps,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
