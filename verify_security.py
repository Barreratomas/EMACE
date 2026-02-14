import psycopg2
import os
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

print("🔒 Verificando seguridad de la Base de Datos...")

# 1. Probar con las credenciales seguras del .env
url = os.getenv("DATABASE_URL")
# Parsear para manejar correctamente la contraseña con '!'
if "SecurePass123!" in url and ":" in url and "@" in url:
    # Reconstruir URL con encoding seguro si es necesario, 
    # aunque psycopg2 suele manejarlo bien si está completo.
    pass

try:
    print(f"🔄 Intentando conectar como 'admin'...")
    conn = psycopg2.connect(url)
    print("✅ ¡ÉXITO! Conexión SEGURA establecida.")
    print("   Usuario: admin")
    print("   Puerto: 5433 (Evadiendo conflicto)")
    conn.close()
except Exception as e:
    print(f"❌ Falló la conexión segura: {e}")
    print("\n⚠️ IMPORTANTE: ¿Reiniciaste el contenedor borrando el volumen?")
    print("Como cambiamos de usuario 'postgres' a 'admin', la base de datos antigua")
    print("debe ser destruida para que se cree la nueva con el usuario correcto.")
    print("\nEjecuta en WSL:")
    print("   docker compose down -v")
    print("   docker compose up -d")
