import os
import sys
import subprocess
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).parent.absolute()
VENV_DIR = BASE_DIR / "venv"



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

    print(f"Directorio de Trabajo: {cwd}")
    print(f"Ejecutando: {command}")
    print("-" * 40)
    
    try:
        subprocess.run(command, cwd=cwd, shell=True, check=True, env=cmd_env)
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando el comando. Código de salida: {e.returncode}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n Detenido por el usuario.")

def start_api(args):
    """Inicia el servidor backend de FastAPI (Uvicorn)."""
    run_command("uvicorn app.interfaces.api.main:app --reload --host 0.0.0.0 --port 8000")


def run_migrate(args):
    """Ejecuta las migraciones de la base de datos para actualizar a la última versión (head)."""
    # Preflight: crear placeholders idempotentes para tablas de checkpoint si la DB está vacía
    try:
        from sqlalchemy import create_engine, text
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            engine = create_engine(db_url, pool_pre_ping=True)
            with engine.begin() as conn:
                conn.execute(text("CREATE TABLE IF NOT EXISTS checkpoint_migrations (v integer PRIMARY KEY);"))
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS checkpoints (
                        thread_id text NOT NULL,
                        checkpoint_ns text DEFAULT '' NOT NULL,
                        checkpoint_id text NOT NULL,
                        parent_checkpoint_id text,
                        type text,
                        checkpoint jsonb NOT NULL,
                        metadata jsonb DEFAULT '{}' NOT NULL,
                        PRIMARY KEY(thread_id, checkpoint_ns, checkpoint_id)
                    );
                """))
                conn.execute(text("CREATE INDEX IF NOT EXISTS checkpoints_thread_id_idx ON checkpoints(thread_id);"))
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS checkpoint_blobs (
                        thread_id text NOT NULL,
                        checkpoint_ns text DEFAULT '' NOT NULL,
                        channel text NOT NULL,
                        version text NOT NULL,
                        type text NOT NULL,
                        blob bytea,
                        PRIMARY KEY(thread_id, checkpoint_ns, channel, version)
                    );
                """))
                conn.execute(text("CREATE INDEX IF NOT EXISTS checkpoint_blobs_thread_id_idx ON checkpoint_blobs(thread_id);"))
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS checkpoint_writes (
                        thread_id text NOT NULL,
                        checkpoint_ns text DEFAULT '' NOT NULL,
                        checkpoint_id text NOT NULL,
                        task_id text NOT NULL,
                        idx integer NOT NULL,
                        channel text NOT NULL,
                        type text,
                        blob bytea NOT NULL,
                        task_path text DEFAULT '' NOT NULL,
                        PRIMARY KEY(thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
                    );
                """))
                conn.execute(text("CREATE INDEX IF NOT EXISTS checkpoint_writes_thread_id_idx ON checkpoint_writes(thread_id);"))
    except Exception as e:
        print(f"⚠️  Preflight de tablas checkpoint omitido: {e}")
    run_command("alembic upgrade heads")

def makemigrations(args):
    """Genera un nuevo script de migración basado en los cambios de los modelos."""
    message = args.message if args.message else "Migración generada automáticamente"
    run_command("alembic upgrade heads")
    run_command(f'alembic revision --autogenerate -m "{message}"')

def migrate_down(args):
    """Revierte la última migración aplicada (rollback)."""
    run_command("alembic downgrade -1")

def migrate_status(args):
    """Muestra el historial de migraciones y la revisión actual de la base de datos."""
    print("Historial de Migraciones:")
    run_command("alembic history --verbose")
    print("\n Revisión Actual:")
    run_command("alembic current")

def run_seed(args):
    run_command("python seed_data.py all")

def reset_db(args):
    run_command("alembic downgrade base")
    run_command("alembic upgrade heads")
    run_command("python seed_data.py all")

def start_scheduler(args):
    """Inicia el planificador de tareas en segundo plano para trabajos proactivos."""
    run_command("python -c \"from app.infrastructure.adapters.scheduler import run_scheduler; run_scheduler()\"")

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
    subparsers.add_parser("api-venv", help="Iniciar backend en venv local (Fuera de Docker)")
    
    # Migraciones (Alembic)
    subparsers.add_parser("migrate", help="Aplicar migraciones pendientes a la base de datos")
    
    make_parser = subparsers.add_parser("makemigrations", help="Crear nueva migración desde cambios en modelos")
    make_parser.add_argument("-m", "--message", help="Mensaje/descripción de la migración", type=str)
    
    subparsers.add_parser("migrate-down", help="Revertir la última migración aplicada")
    subparsers.add_parser("migrate-status", help="Mostrar historial y versión actual de migraciones")
    
    subparsers.add_parser("seed", help="Cargar base de datos con datos de prueba")
    subparsers.add_parser("reset-db", help="Reiniciar base de datos y recargar datos iniciales")
    subparsers.add_parser("scheduler", help="Iniciar planificador de tareas en segundo plano")
    subparsers.add_parser("test", help="Ejecutar pruebas de verificación de API")
    subparsers.add_parser("install", help="Instalar dependencias de requirements.txt")

    args = parser.parse_args()

    # Mapeo de comandos
    commands = {
        "api": start_api,
        "migrate": run_migrate,
        "makemigrations": makemigrations,
        "migrate-down": migrate_down,
        "migrate-status": migrate_status,
        "seed": run_seed,
        "reset-db": reset_db,
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
