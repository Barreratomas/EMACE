# 🏢 Plan de Proyecto Profesional: Ecosistema de Agentes Cognitivos
**Nivel de Complejidad: Enterprise (Arquitectura Escalable)**

Este plan detalla la construcción de un sistema multi-agente robusto, respaldado por infraestructura de datos real (SQL + Vectorial) y patrones de diseño de software profesional.



---

## 🏗️ Fase 1: Infraestructura y Capa de Datos (Data Foundation)
Antes de los agentes, construimos la "memoria" física del sistema. Nada de mocks.

### 1.1 Stack Tecnológico
- **Base de Datos Relacional (SQL)**: PostgreSQL (vía Docker). Para datos transaccionales (usuarios, facturas, productos).
- **Base de Datos Vectorial**: Qdrant o ChromaDB (vía Docker). Para memoria semántica y RAG.
- **ORM & Migraciones**: SQLModel (Pydantic + SQLAlchemy) + Alembic.
- **Modelos LLM**: Asignación específica por rol (ver `asignacion_de_modelos_llm_para_ecosistema_multi_agente.md`) vía OpenRouter.

### 1.2 Tareas
- [x] **Configurar Docker Compose**: Crear `docker-compose.yml` levantando PostgreSQL y Qdrant/Chroma.
- [x] **Modelado de Datos (SQL)**:
    - Definir modelos en `app/core/database/models.py`: `User`, `Invoice`, `Ticket`, `AuditLog`.
- [x] **Sistema de Migraciones**: Inicializar Alembic para control de versiones del esquema de BD.
- [x] **Conexión Vectorial**: Configurar cliente de Vector DB en `app/core/vector/client.py`.

---

## 🧠 Fase 2: Servicios Cognitivos (RAG y Memoria)
Implementación de la memoria a largo plazo y recuperación de información.

### 2.1 Módulos
- [x] **Servicio de Ingesta (RAG)**:
  - [x] Script para procesar PDFs/MDs, dividir en chunks y generar embeddings (`app/core/rag/ingestion.py`).
  - [x] Almacenamiento en Qdrant (colección `knowledge_base`).
- [x] **Motor de Búsqueda Híbrida**:
  - [x] Clase `HybridRetriever` que combine búsqueda vectorial y filtros de metadatos (`app/core/rag/retriever.py`).
- [x] **Memoria Episódica**:
  - [x] Sistema para guardar interacciones pasadas en la BD Vectorial (`app/core/memory/episodic.py`).

---

## 👔 Fase 3: El Supervisor (Orquestación Jerárquica)
Migración de grafo lineal a arquitectura "Hub & Spoke" (Estrella).

- [x] **Estado Global Avanzado**: `SupervisorState` persistido en Postgres (Checkpointer).
- [x] **Agente Supervisor**: Un LLM "Router" que decide a qué sub-agente llamar o si responder directamente.
- [x] **Manejo de Hilos**: Soporte para múltiples conversaciones simultáneas persistentes.

---

## 🛠️ Fase 4: Agentes Especialistas con Herramientas Reales (Tools)
Los agentes interactúan con la infraestructura de la Fase 1.

### 4.1 Agente de Facturación (Billing)
- [x] **Tool SQL**: `get_client_invoices(client_id)` (Consulta real a Postgres).
- [x] **Tool Análisis**: `check_invoice_status(invoice_id)`.

### 4.2 Agente Técnico
- [x] **Tool Knowledge Base**: `search_technical_docs(query)` (Consulta a Vector DB).
- [x] **Tool Diagnóstico**: Consulta simulada a logs de sistema (pero estructurada).

### 4.3 Agente de Ventas/Soporte
- [x] **Tool Catálogo**: Búsqueda híbrida de productos (SQL + Vector).

---

## 🔄 Fase 5: Ciclo de Mejora Continua (Self-Correction Loop)
- [x] **Agente QA Crítico**: Evalúa respuestas y, si fallan, genera un reporte estructurado.
- [x] **Pipeline de Aprendizaje**: Lecciones aprendidas persistentes en Qdrant.



---

## 🔮 Fase 6: Proactividad y Acción Real (El "Factor Wow")
Implementación de capacidades autónomas y conexión con el mundo exterior.

### 6.1 Módulo de Proactividad
- [x] **Scheduler Multi-Tenant**: Jobs por `user_id` con aislamiento, límites y reintentos.
- [x] **Monitores de Negocio**: Reglas por tienda (stock bajo, vencimientos, citas próximas).
- [x] **Trigger Inverso**: Notificaciones por canal con contexto de usuario y plantilla.
- [x] **Idempotencia y Observabilidad**: Evitar duplicados y registrar métricas por tenant.

### 6.2 Gestión de Inventario y Catálogo (Admin Tools)
- [x] **Tools CRUD Multi-Tenant**: Crear, editar y archivar productos con `user_id`.
- [x] **Gestión de Stock**: Ajustes de inventario con umbrales y pausa automática.
- [x] **Panel Admin**: Vista por tienda, filtros por estado y acciones masivas.
- [x] **Alertas Operativas**: Notificación al vendedor por eventos críticos.

### 6.3 Comunicaciones Externas
- [ ] **Canales de Comunicación**: Email y mensajería con plantillas y trazabilidad.
- [ ] **Herramientas de Notificación**: Cotizaciones, alertas y recordatorios por tenant.
- [ ] **Calendario**: Integración para agendar citas por usuario y cliente final.
- [ ] **Auditoría de Eventos**: Historial de envíos y estado por canal.

---




## 🧠 Fase 7: Refactorización del Supervisor (Nivel Enterprise)
Elevando la arquitectura del orquestador para robustez, mantenibilidad y observabilidad (Feedback Loop).

- [x] **Estandarización y Robustez de Modelos**:
    - [x] Migración a `stepfun/step-3.5-flash:free` en todos los agentes para reducir latencia.
    - [x] Implementación de **Sanitización de Contexto** (Context Sanitization) en `factory.py` y `supervisor.py` para eliminar prefijos alucinados y contaminación de identidad.
- [x] **Estrategia Híbrida de Parsing (Supervisor)**:
    - [x] **Regex Extraction**: Extracción quirúrgica de bloques JSON `\{.*\}` para tolerar texto adicional del modelo.
    - [x] **Fallback Heurístico**: Redirección automática a `Sales` cuando el modelo falla en generar JSON y responde conversacionalmente (ej: saludos).
    - [x] **Few-Shot Prompting**: Ejemplos explícitos en el System Prompt para enseñar el formato JSON correcto en casos triviales.
- [x] **Enrutamiento Inteligente con Confianza**:
    - [x] Implementar `confidence_score` (0.0 - 1.0) en la decisión de ruteo.
    - [x] Lógica de umbral: Si el modelo responde texto plano, se asume intención general y se rutea a Sales.
- [x] **Manejo de Errores y Fallbacks**:
    - [x] Eliminar `except: FINISH` genérico y agregar logging detallado.
    - [x] Fallback a "Modo Seguro" (Sales o FINISH controlado) en lugar de crash.
- [x] **Motor de Políticas (Policy Engine)**:
    - [x] Implementar `Guardrails` explícitos en código (Sanitización de entradas, Lógica de QA Loop y anti-bucles).


---


## 🏢 Fase 8: Multi-Tenancy y Centralización de Datos (Seguridad Enterprise)
Transformación del sistema de "Single User" a una plataforma SaaS segura para múltiples inquilinos (Modelo B2B2C).

- [x] ** Fase 8.1:Refactorización de Modelos de Datos (B2B2C)**:
    - [x] **Separación de Roles**: Diferenciar claramente entre `User` (Dueño de tienda/Vendedor) y `Customer` (Cliente final).
    - [x] **Nuevo Modelo `Customer`**: Crear tabla `Customer` vinculada a `User` (Foreign Key `user_id`) para que cada vendedor gestione su propia cartera de clientes.
    - [x] **Propiedad de Inventario**: Agregar `user_id` a la tabla `Product`. Un producto pertenece a un vendedor específico, no al sistema global.
    - [x] **Transacciones Aisladas**: Actualizar `Invoice` y `Ticket` para vincularse a un `Customer` específico y validar que pertenezcan al `User` en sesión.

- [x] ** Fase 8.2: Aislamiento de Datos (Data Isolation)**:
    - [x] **Vector DB (Qdrant)**: Refactorizar `EpisodicMemory` y `Retriever` para obligar el filtro `user_id` en TODAS las consultas (evitar fugas de contexto entre vendedores).
    - [x] **SQL DB (Postgres)**: Implementar "Tenant Context" en los Repositorios. Todas las queries deben filtrar automáticamente por `user_id`.
    - [x] **Auditoría**: Crear tabla `ChatHistory` con columnas `user_id` (Vendedor) y `session_id` (Contexto) para trazabilidad legal.

- [x] ** Fase 8.3: Gestión de Identidad (Auth)**:
    - [x] Actualizar API `POST /chat` para recibir y validar `user_id` (preparación para JWT).
    - [x] Middleware de Contexto: Inyectar `user_id` en el `config` de LangGraph automáticamente.

- [x] ** Fase 8.4: Escalabilidad de Memoria**:
    - [x] Implementar política de retención: Archivar memorias antiguas (> 6 meses) a almacenamiento frío (Cold Storage).
    - [x] Optimización de Indices: Crear índices compuestos en Qdrant por `(user_id, timestamp)`.

---

## 🔐 Fase 9: Sistema de Autenticación y Autorización (Seguridad Enterprise)
Implementación de un sistema completo de autenticación JWT con roles, autorización basada en recursos y protección contra vulnerabilidades comunes.

### 9.1 Infraestructura de Autenticación
- [x] **Modelo de Usuario Extendido**: Agregar campos de seguridad al modelo `User` (password_hash, is_active, role, last_login, failed_attempts).
- [x] **Gestión de Sesiones**: Implementar refresh tokens con almacenamiento seguro en base de datos.
- [x] **Roles y Permisos**: Sistema RBAC (Role-Based Access Control) con roles dinámicos creados y gestionados por el `admin`. Se elimina el rol `customer` del ámbito web.
- [x] **Rate Limiting**: Protección contra fuerza bruta en endpoints de autenticación.

### 9.2 Seguridad de Contraseñas
- [x] **Hashing Robusto**: bcrypt con salt rounds >= 12 (vía passlib) para almacenamiento seguro de contraseñas.
- [x] **Política de Contraseñas**: Requisitos mínimos (12 caracteres, mayúsculas, minúsculas, números y símbolos).
- [x] **Recuperación de Contraseña**: Tokens seguros de un solo uso con expiración controlada (JWT).
- [x] **MFA (Multi-Factor Authentication)**: Preparación del modelo `User` con campos `mfa_enabled` y `totp_secret`.

### 9.3 JWT y Gestión de Tokens
- [x] **Access Tokens**: JWT de corta duración (30 minutos) con claims específicos del negocio (sub, role, permissions, type).
- [x] **Refresh Tokens**: Tokens de larga duración (7 días) almacenados de forma segura en la base de datos.
- [x] **Revocación de Tokens**: Sistema de invalidación en base de datos (`is_revoked`) para logout inmediato.
- [x] **Rotación de Tokens**: Lógica implementada en `AuthRepository` para generar nuevos tokens invalidando los anteriores.

### 9.4 Autorización y Control de Acceso
- [x] **Autorización por Recursos**: Verificación de permisos a nivel de objeto integrada en los endpoints de inventario (Multi-Tenant).
- [x] **Middleware de Autenticación**: Dependencias de FastAPI (`get_current_user`) para validación automática de tokens en rutas protegidas.
- [x] **Contexto de Usuario**: Inyección automática del usuario autenticado en el contexto de LangGraph y memoria episódica.
- [x] **RBAC (Role-Based Access Control)**: Implementado verificador de roles (`RoleChecker`) para restringir acciones según el rol del usuario.

### 9.5 Protección contra Ataques Comunes
- [x] **CORS Seguro**: Configuración restrictiva de orígenes permitidos en `app/api/main.py`.
- [x] **Headers de Seguridad**: Implementación de `SecurityHeadersMiddleware` (HSTS, CSP, X-Frame-Options, etc.).
- [x] **Validación de Entradas**: Uso estricto de SQLModel/Pydantic para prevenir SQL Injection y validación de tipos.
- [x] **XSS Prevention**: Sanitización automática de strings en modelos Pydantic usando `bleach`.
- [x] **CSRF Protection**: Infraestructura configurada con `fastapi-csrf-protect` (preparado para Fase 10).

### 9.6 API de Autenticación
- [x] **Endpoints de Auth**: `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/me`.
    - [x] **Esquemas de Datos**: Login, Register, PasswordChange, UserUpdate.
    - [x] **Validación**: Email único, política de contraseñas (12+ caracteres).
    - [x] **Rate Limiting**: Protección contra fuerza bruta en login/register.
    - [x] **Seguridad de Tokens**: Almacenamiento y revocación de Refresh Tokens.
- [x] **Validación de Email**: Verificación de formato y existencia de dominio.
- [x] **Gestión de Perfil**: Actualización segura de información del usuario.
- [x] **Cambio de Contraseña**: Endpoint seguro para actualización de credenciales.

### 9.7 Integración con el Sistema Multi-Agente
- [x] **User Context en Agentes**: Los agentes deben conocer el contexto del usuario autenticado.
- [x] **Aislamiento Multi-Tenant**: Cada usuario solo accede a sus propios datos y agentes.
- [x] **Permisos por Agente**: Control de qué agentes puede usar cada rol de usuario.
- [x] **Auditoría de Agentes**: Registro de todas las interacciones de agentes con usuario identificado.

---

## 📱 Fase 10: Ecosistema para el Cliente Final (B2C via Telegram)
Ampliación de la arquitectura para permitir que el `Customer` interactúe directamente con el sistema a través de canales de mensajería.

### 10.1 Infraestructura de Mensajería (Telegram)
- [x] **Bot de Telegram Multi-Tenant**: Configuración de Webhooks y pooling para manejar mensajes de múltiples clientes.
- [x] **Vinculación Customer-Telegram**: Sistema para asociar el `chat_id` de Telegram con el `id` de el `Customer` en la base de datos SQL.
- [x] **Mapeo de Contexto**: Lógica para identificar a qué `User` (Vendedor) pertenece el bot de Telegram al que escribe el cliente.

### 10.2 Agente de Atención al Cliente (Customer Agent)
- [x] **Nuevo Especialista "Customer Support"**: Agente optimizado para interactuar con clientes finales con un tono servicial y comercial.
- [x] **Herramientas para Clientes (Customer Tools)**:
    - [x] `browse_catalog`: Versión pública del catálogo filtrada por la tienda del vendedor. (Usando `search_product_catalog`)
    - [x] `create_order`: Capacidad para que el cliente inicie un proceso de compra/pedido.
    - [x] `check_my_invoices`: El cliente solo puede ver sus propias facturas.
    - [x] `book_appointment`: Interfaz para que el cliente agende una cita directamente.
- [x] **Aislamiento de Seguridad Estricto**: Garantizar que el agente del cliente NUNCA tenga acceso a herramientas administrativas (`Inventory CRUD`, `Audit Logs`, etc.).

### 10.3 Flujo de Venta y Transacciones (E-commerce Lite)
- [x] **Carrito de Compras Virtual**: Persistencia del estado del pedido en la base de datos durante la sesión de chat.
- [x] **Generación Automática de Facturas**: Al confirmar la compra en Telegram, el sistema crea el registro en la tabla `Invoice`.
- [x] **Notificaciones de Estado**: Envío proactivo de actualizaciones de pedido al cliente vía Telegram.

### 10.4 Modelo de Integración Telegram por Vendor
- [x] **Entidad y Modelo de Datos**:
  - [x] Extender el modelo de `User`/`Vendor` con entidad `VendorTelegramIntegration`:
    - Campos: `vendor_id`, `bot_token` (cifrado), `bot_username`, `webhook_secret`, `is_active`, `last_error`, timestamps.
    - Índices por `vendor_id` y `bot_username` para resolución rápida.
  - [x] Auditoría de cambios (alta/baja/rotación de token) para trazabilidad.

### 10.5 Infraestructura de Webhooks Multi-Tenant
- [x] **Endpoint de Entrada Unificado**:
  - [x] Endpoint FastAPI: `POST /telegram/webhook/{vendor_public_id}/{webhook_secret}`.
    - `vendor_public_id`: identificador público o slug del Vendor.
    - `webhook_secret`: token aleatorio generado por el sistema (no es el `bot_token`) que se incluye en la URL configurada en BotFather.
- [x] **Resolución de Contexto y Ruteo**:
  - [x] Determinar Vendor a partir de `{vendor_public_id}`.
  - [x] Cargar integración Telegram del Vendor, validar que `webhook_secret` coincide y que `is_active = true`.
  - [x] Enrutar el `Update` al grafo de agentes con contexto de Vendor + Customer (`user_id` + `customer_id`).
  - [x] Reutilizar la misma infraestructura de procesamiento de updates que el Bot multi-tenant general (Fase 10.1), pero inyectando el origen `telegram_vendor_bot`.

### 10.6 Onboarding y Panel de Integración para Vendors
- [x] **Backend: Integración de Bot por Vendor**:
  - [x] Creación y actualización de `VendorTelegramIntegration` a partir de credenciales obtenidas desde BotFather.
  - [x] Configuración automática del webhook de Telegram apuntando a `https://<backend>/api/v1/telegram/webhook/{vendor_public_id}/{webhook_secret}`.
  - [x] Endpoint `POST /vendors/me/integrations/telegram/test`:
    - Enviar mensaje de prueba ("Tu bot está conectado a EMACE") al Vendor para confirmar conectividad.
- [x] **Frontend: Settings → Canales → Telegram**:
  - [x] Panel de estado del bot:
    - Visualización de `bot_username`, webhook redactado, estado (activo/pausado/eliminado) y último error.
    - Acciones de gestión: pausar, reanudar, regenerar secreto de webhook y eliminar integración.
  - [x] Integración con Modo C:
    - Uso de la sesión MTProto (userbot) para crear automáticamente el bot y vincularlo a la tienda sin pegar manualmente el `bot_token`.

### 10.7 Seguridad, Operación y Observabilidad de Bots
- [x] **Seguridad y Cumplimiento**:
  - [x] Cifrado de `bot_token` en base de datos usando clave maestra del backend (por ejemplo, Fernet con `SECRET_KEY` derivado).
  - [x] Nunca loguear `bot_token` ni la URL completa del webhook (solo partes redacted).
  - [x] Rate limiting específico por Vendor y por Bot en el endpoint de webhook para evitar abuso.
  - [ ] Validaciones de origen:
    - Opcional: verificación de IPs de Telegram (lista oficial) y/o uso de firewall a nivel de infraestructura.
  - [x] Rotación de credenciales:
    - Proceso para que el Vendor pueda reemplazar su `bot_token` (rotación) sin perder histórico de conversaciones.
- [x] **Operación y Observabilidad**:
  - [x] Métricas por Vendor/Bot:
    - Número de mensajes entrantes/salientes, errores de webhook, tiempo medio de respuesta.
  - [x] Health-check de integraciones:
    - Job del scheduler que revisa integraciones con `last_error` reciente y envía notificación al Vendor (email o dashboard) para tomar acción.
  - [x] Panel administrativo:
    - Vista para el administrador de la plataforma con listado de Vendors y estado de sus bots (con posibilidad de suspender integración ante abuso).

---

### 10.8 Onboarding sin BotFather: Estrategias y Plan de Implementación

Objetivo: reducir la fricción de onboarding para vendors priorizando “un bot por vendor”, manteniendo cumplimiento y robustez.

Decisión recomendada:
- Modo B (Default): Asistente guiado. Cada vendor vincula su propio bot pegando el token de BotFather. Automatizamos verificación, setWebhook, rotación y diagnóstico.
- Modo C (Opcional): Automatización avanzada vía MTProto userbot para “crear” el bot desde la UI, bajo consentimiento expreso y salvaguardas legales/técnicas.

> Nota: Se desaconseja el uso de un bot único multi‑tenant operado por la plataforma para producción (se elimina como default).

#### Modo B — Asistente Guiado con Deep Links a BotFather (Deprecated)
- Descripción (diseño original, hoy deprecado y removido del código):
  - El vendor era dueño de su bot y pegaba manualmente el `bot_token` de BotFather en la UI.
- Estado actual:
  - El flujo de vinculación manual de token y sus endpoints asociados (`POST /vendors/me/integrations/telegram/link`, `DELETE /vendors/me/integrations/telegram`) se considera legado y fue retirado del backend y del frontend.
  - La creación y vinculación de bots nuevos se realiza exclusivamente a través de Modo C (auto‑create vía BotFatherOrchestrator).

#### Modo C — Automatización Avanzada (MTProto Userbot) [Opt‑in]
- Descripción:
  - La plataforma actúa como cliente MTProto autenticado (userbot) para automatizar conversación con BotFather en nombre del usuario. Se requiere login del usuario en Telegram (por QR/OTP) dentro de la UI.
- Consideraciones:
  - Riesgo de incumplimiento de Términos de Telegram; solo bajo consentimiento explícito.
  - Requiere protección estricta de credenciales y sesión efímera.
  - Mantenibilidad baja ante cambios de BotFather.
- Implementación (solo si se aprueba):
  - Servicio que inicia sesión MTProto para ese usuario (sesión efímera).
  - Secuencia: `/newbot` → nombre → username → lectura de token → cierre de sesión.
  - Auditoría completa y purga inmediata de sesión.
- Pros:
  - Casi “one‑click” para crear bot.
- Contras:
  - Riesgo legal y técnico alto. No recomendado como default.

#### Cambios Técnicos Propuestos
- Modelado:
  - Persistencia de integración por vendor (`VendorTelegramIntegration`) con cifrado de `bot_token` y `webhook_secret`.
- Endpoints activos:
  - `POST /vendors/me/integrations/telegram/test` → envío de prueba para diagnóstico.
  - `POST /vendors/me/integrations/telegram/bot/pause` → pausa el bot y desactiva el webhook.
  - `POST /vendors/me/integrations/telegram/bot/resume` → reanuda el bot y restablece el webhook.
  - `PATCH /vendors/me/integrations/telegram/bot` → permite regenerar el `webhook_secret`.
  - `DELETE /vendors/me/integrations/telegram/bot` → elimina lógicamente la integración y corta el webhook.
- Creación de integración:
  - La creación inicial de `VendorTelegramIntegration` se realiza a través de Modo C, usando el orquestador con BotFather para obtener el token y configurar el webhook sin intervención manual del vendor.
- Seguridad:
  - Cifrado de `bot_token` con clave maestra; nunca loguear secretos ni URL completa del webhook.
  - Rate limiting por vendor y por bot en el webhook; validaciones y redacción de logs.
- Observabilidad:
  - Métricas por vendor/bot: mensajes entrantes/salientes, errores, latencia, último update.
- Testing:
  - Unit tests de verificación `getMe`, `setWebhook`, cifrado/rotación de tokens y manejo de errores.
  - E2E: creación automática → probar → pausar/reanudar → eliminar (incluye fallos de Telegram).

#### Roadmap de Despliegue
1) Activar Modo C (auto‑create vía userbot MTProto) como flujo por defecto para vendors.  
2) Mantener únicamente soporte de lectura sobre integraciones legacy ya existentes (si aplica), sin exponer nuevamente el flujo Modo B.

#### Nota sobre “crear bots sin Telegram”
No existe API oficial pública para crear bots sin mediar @BotFather. La vía elegida en este proyecto es:
- Automatizar BotFather vía MTProto (Modo C) bajo consentimiento, con riesgos y salvaguardas, manteniendo siempre la propiedad del bot en manos del vendor y evitando la inserción manual del token en la UI.

## 🔌 Fase 10.10: Backend de Integración por Vendor
- Alcance
  - Modelo `VendorTelegramIntegration` con cifrado de `bot_token` y `webhook_secret`, unicidad `bot_username`.
  - Endpoints base actuales: `POST /vendors/me/integrations/telegram/test`, `POST /vendors/me/integrations/telegram/bot/pause`, `POST /vendors/me/integrations/telegram/bot/resume`, `PATCH /vendors/me/integrations/telegram/bot`, `DELETE /vendors/me/integrations/telegram/bot`.
  - Auditoría de eventos críticos (creación vía BotFatherOrchestrator, pausa, reanudación, actualización de propiedades, delete) sin exponer secretos.
- Tareas
  - [x] Implementar modelo y repositorio con cifrado.
  - [x] Implementar creación de integración a partir del token obtenido automáticamente desde BotFather (Modo C).
  - [x] Implementar endpoints de gestión (`test`, `pause`, `resume`, `patch`, `delete`) con semántica consistente de estados.
  - [x] Manejo de errores operativo (mensajes claros) y timeouts/reintentos.

## 🧭 Fase 10.11: UX de Integración por Vendor (Modo C)
- Alcance
  - Panel de estado del bot por vendor, integrado con Modo C (auto‑create) y acciones de mantenimiento.
  - Acciones de mantenimiento: “Probar envío”, “Pausar/Reanudar”, “Regenerar secreto de webhook”, “Eliminar integración”.
- Tareas
  - [x] Construir UI con validaciones y toasts.
  - [x] Implementar UI de estados (activo/pausado/eliminado, último error) y webhook redactado.
  - [x] Flujos de confirmación para pausa, reanudación, regeneración de secreto y eliminación lógica.

## 📈 Fase 10.12: Observabilidad y SRE
- Alcance
  - Métricas por Vendor/Bot (entradas, salidas, errores, latencia, último update).
  - Health‑check programado con notificaciones a Vendor.
  - Panel admin global de integraciones.
- Tareas
  - [x] Exportar métricas y exponerlas en panel interno.
  - [x] Implementar job de health‑check con reintentos.
  - [x] Construir panel admin con suspensión de bots.

## 🔐 Fase 10.13: Seguridad y Cumplimiento
- Alcance
  - Rotación de clave maestra y procedimiento de re‑cifrado.
  - Protocolo de respuesta ante incidentes (revocar token, desactivar integración, comunicación).
- Tareas
  - [x] Documentar y automatizar rotación de claves.
  - [x] Implementar redacción estricta de logs y verificaciones de configuración.
  - [x] Definir y ensayar playbooks de incidentes.

## ✅ Fase 10.14: Testing y Rollout
- Alcance
  - Suite de tests (unit y E2E) y despliegue controlado con feature flags.
- Tareas
  - [x] Unit: `getMe`, `setWebhook`, unicidad `bot_username`, cifrado/rotación, errores.
  - [x] E2E: vincular → probar → rotar → desvincular → revincular (incluye fallos de Telegram).
  - [x] Activar feature flag y comunicar migración a Vendors.

## ⚙️ Fase 10.15 (Default actual): MTProto Userbot (Modo C)
- Alcance
  - Legal/consentimiento, infraestructura MTProto efímera, orquestación con BotFather, seguridad y auditoría.
- Tareas
  - [x] Definir modelo de opt‑in legal para vendors (términos Modo C).
  - [x] Añadir flags de configuración y kill switch de Modo C en backend.
  - [x] Implementar endpoint de consentimiento versionado y registro en AuditLog.
  - [x] Diseñar estrategia de fallback controlado (p. ej. desactivar temporalmente auto‑create y mantener integraciones ya existentes) sin reintroducir el flujo Modo B.

---

## 🎛️ Fase 10.16: UX Frontend Telegram Pro (Modo C)
- Alcance
  - Interfaz gráfica avanzada para gestionar integraciones Telegram por vendor (Bots creados/vinculados vía Modo C).
  - Soporte visual para estados, errores y acciones críticas.
- Tareas
  - [x] Extender Settings › Telegram con sección dedicada a Modo C (Userbot + auto‑create).
  - [x] Implementar UI de consentimiento explícito de Modo C (checkbox + resumen de términos + link legal).
  - [x] Añadir visualización de estado por vendor: health, latencia estimada, últimos errores, fecha de último mensaje.
  - [x] Diseñar flujos de pausa, reanudación, regeneración de secreto y eliminación con diálogos de confirmación consistentes.
  - [x] Añadir avisos claros de riesgos y límites de Modo C (beta / opt‑in avanzado).

## 🧪 Fase 10.17: Testing Avanzado Telegram (Backend + Frontend)
- Alcance
  - Consolidar pruebas automáticas e2e y unitarias para todos los flujos relevantes de Telegram.
- Tareas
  - [x] Añadir tests unitarios de `_is_mtproto_allowed` y de los códigos de error (mtproto_unavailable, consent_not_accepted).
  - [x] Mockear llamadas a Telegram API (httpx) para simular `getMe`, `setWebhook` y errores de red de forma determinista.
  - [x] Incorporar tests de integración que cubran: consentimiento Modo C, fallback a Modo B y kill switch.
  - [x] Crear pruebas de frontend (Playwright o equivalente) para el wizard de Telegram y los flujos de consentimiento.
  - [x] Integrar estos tests en el pipeline de CI, marcando los que dependan de servicios externos como opcionales o con mocks.

## 🚀 Fase 10.18: Operaciones, Observabilidad y Playbooks de Producción
- Alcance
  - Preparar el entorno de producción para operar Telegram a escala, con visibilidad y resiliencia.
- Tareas
  - [x] Definir y versionar variables de entorno y secretos para Telegram (Bot API y Modo C) en cada entorno (dev, staging, prod).
    - Variables base alineadas con `Settings` del backend: `TELEGRAM_ENABLED`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_DEFAULT_CHAT_ID`, `TELEGRAM_MTPROTO_ENABLED`, `TELEGRAM_MTPROTO_KILL_SWITCH`, `TELEGRAM_MTPROTO_ALLOWED_VENDORS`.
    - Esquema por entorno:
      - **Dev**: `.env.dev` con tokens de prueba y `TELEGRAM_ENABLED=true`, `TELEGRAM_MTPROTO_ENABLED=false`.
      - **Staging**: `.env.staging` con tokens reales de pre‑producción, `TELEGRAM_MTPROTO_ENABLED=true` solo para vendors piloto.
      - **Prod**: configuración vía gestor de secretos (no en archivos), con `TELEGRAM_ENABLED=true`, `TELEGRAM_MTPROTO_KILL_SWITCH` disponible para apagado global.
    - Versionado y control de cambios a través de IaC / configuración de despliegue (commit de referencia + registro de rotaciones).
  - [x] Crear dashboards en la plataforma de observabilidad elegida con métricas clave de Telegram (tráfico, errores, latencia, health checks).
    - Dashboard **Telegram Overview**:
      - Mensajes entrantes/salientes por minuto (por vendor y total).
      - Errores de webhook por tipo (4xx, 5xx, timeouts, `telegram_api_unreachable`).
      - Latencia p50/p95/p99 del procesamiento de mensajes (a partir de métricas de `AuditLog` y jobs de health‑check).
      - Estado de integraciones: número de bots `healthy`, `degraded`, `inactive` (basado en la API admin `/telegram/admin/integrations`).
    - Dashboard **MTProto Modo C**:
      - Vendors con Modo C habilitado vs total.
      - Incidentes recientes asociados a Modo C (abuso, bloqueos, kill switch activado).
  - [x] Formalizar playbooks de incidentes: pérdida de token, abuso de userbot, timeouts de Telegram, quota limits.
    - **Pérdida/filtración de token de bot**:
      1. Desactivar integración desde panel admin (suspender vendor afectado).
      2. Rotar `bot_token` en BotFather.
      3. Usar flujo de rotación en Settings › Telegram para actualizar integración (endpoint `link` con nuevo token).
      4. Revisar logs de actividad y notificar al vendor con resumen del incidente.
    - **Abuso de userbot / Modo C**:
      1. Activar `TELEGRAM_MTPROTO_KILL_SWITCH=true` para detener todas las sesiones de userbot.
      2. Revisar vendors Modo C (panel admin) y aislar los que presenten patrones de abuso.
      3. Comunicar restricciones temporales y pasos de corrección.
    - **Timeouts/errores de Telegram / quota limits**:
      1. Detectar spike en errores 429/5xx y timeouts vía dashboards.
      2. Activar degradación suave: fallback a Modo B o suspender temporalmente envíos proactivos.
      3. Ajustar rate limits y revisar conectividad (red, DNS, túneles).
  - [x] Establecer alertas proactivas (threshold de errores, p95 de latencia, fallos de health‑check repetidos).
    - Alertas recomendadas:
      - Error rate de webhook > X% durante N minutos (por vendor y global).
      - Latencia p95 del procesamiento de mensajes > umbral definido (ej. 2s) durante ventana de tiempo.
      - Health‑check fallido para una integración específica más de M veces consecutivas.
      - Activación de `TELEGRAM_MTPROTO_KILL_SWITCH` o cambios en `TELEGRAM_MTPROTO_ALLOWED_VENDORS`.
    - Canal de notificación: equipo SRE/operaciones (Slack/Email) + anotación automática en panel de incidentes.
  - [x] Documentar procedimiento de rotación de claves y tokens de bots en producción paso a paso.
    - Flujo estándar de rotación:
      1. Programar ventana de mantenimiento con el vendor (si aplica).
      2. Rotar token en BotFather y guardar nuevo `bot_token` de forma segura.
      3. Acceder a Settings › Telegram del vendor y usar acción de “Rotar token” (reutilizando `/vendors/me/integrations/telegram/link`).
      4. Verificar que el webhook quede en estado `healthy` y que los mensajes de prueba funcionen (botón “Enviar mensaje de prueba”).
      5. Revocar el token antiguo en BotFather y actualizar documentación interna (registro de rotación y estado de integraciones).

## 📣 Fase 10.19: Producto, Onboarding y Comunicación a Vendors
- Alcance
  - Empaquetar la integración de Telegram como una feature de producto entendible y accionable.
- Tareas
  - [x] Definir segmentos de vendors elegibles para Modo C (beta cerrada, enterprise, etc.).
    - Segmentos recomendados:
      - **Beta cerrada**: vendors con alto volumen de tickets o chats mensuales, equipo técnico interno y disposición a co‑diseñar el flujo (early adopters).
      - **Enterprise**: cuentas con contrato de soporte avanzado donde Modo C aporta alto impacto en automatización.
      - **Standard**: vendors que sólo usan Modo B (Bot API) y no requieren userbot; Modo C permanece oculto o bajo solicitud.
    - Criterios de elegibilidad:
      - Historial de cumplimiento de términos y baja tasa de incidentes.
      - Capacidad de gestionar riesgos legales de userbots en su jurisdicción.
  - [x] Crear material de onboarding para vendors: guía rápida de vinculación de bot y mejores prácticas.
    - Estructura de la guía rápida:
      - Paso 1: Crear bot en BotFather y obtener el `bot_token`.
      - Paso 2: Vincular el bot desde Settings › Telegram (Modo B), con screenshots de cada paso.
      - Paso 3: Probar el bot con mensajes de ejemplo y verificar el estado en el panel (health, latencia, últimos errores).
      - Sección de buenas prácticas:
        - Mantener tokens seguros y rotarlos regularmente.
        - Definir un único responsable interno de la integración.
        - No reutilizar el mismo bot para otros sistemas externos que puedan generar conflictos.
    - Formatos previstos:
      - Página de documentación en la sección de ayuda de la plataforma.
      - Versión PDF ligera para enviar por email a nuevos vendors.
  - [x] Diseñar mensajes dentro del dashboard para anunciar la feature, estados de rollout y cambios de política.
    - Mensajes clave:
      - Banner en el dashboard anunciando disponibilidad de integración con Telegram (Modo B) y Modo C en beta cerrada.
      - Etiquetas de estado en Settings › Telegram indicando:
        - “Disponible para tu plan” / “Disponible bajo solicitud” / “Beta cerrada”.
      - Mensajes contextuales en el wizard cuando se cambia el estado de integración (vinculado, degradado, suspendido).
    - Uso de Notification Center:
      - Notificaciones in‑app cuando:
        - Se active una nueva capacidad de Telegram para un vendor.
        - Cambien los términos legales o de uso aceptable.
        - Se deprequen comportamientos antiguos (por ejemplo, cambiar el endpoint de webhook).
  - [x] Establecer un circuito de feedback (encuestas, NPS de la feature, canal dedicado) para iterar sobre la integración.
    - Canales de feedback:
      - Encuesta breve tras X días de uso de la integración (enlace en Notification Center o email).
      - Pregunta de NPS específica para la feature (“¿Qué probabilidad hay de que recomiendes la integración de Telegram a otro operador?”).
      - Canal dedicado (email o espacio privado) para vendors de Modo C beta.
    - Ciclo de iteración:
      - Recopilar feedback trimestralmente.
      - Priorizar mejoras en base a volumen de solicitudes y criticidad (fiabilidad vs. UX).
      - Comunicar en el dashboard los cambios realizados (“What’s new” de Telegram).
  - [x] Revisar implicancias de pricing/planes comerciales asociadas al uso avanzado de Telegram.
    - Lineamientos de pricing:
      - Modo B incluido en planes estándar, con límites razonables de tráfico.
      - Modo C disponible sólo para planes avanzados o como add‑on, dada la infraestructura extra y el riesgo operativo.
      - Posible tarificación por volumen de mensajes procesados y uso intensivo de MTProto.
    - Ajustes de comunicación:
      - Indicar de forma clara en la página de pricing cuáles son las capacidades de Telegram incluidas en cada plan.
      - Añadir mensajes dentro de Settings › Telegram cuando una funcionalidad requiera un upgrade de plan o la activación de Modo C.

## 🧩 Fase 10.20: Implementación Técnica Modo C (Userbot MTProto)
- Alcance
  - [x] Implementar un cliente MTProto por vendor (userbot) con opt‑in, aislado y controlado por flags (scaffolding y gates).
- Arquitectura y Persistencia
  - [x] Modelo por vendor para credenciales MTProto (número, device, session_string cifrado, estado).
  - [x] Cifrado y rotación de `session_string` con utilidades existentes (mismo esquema que bot_token).
  - [x] Estado por vendor: `mtproto_enabled`, `mtproto_status`, `last_error`, `last_heartbeat_at`.
  - [x] Storage de sesión: en DB cifrada; evitar archivos locales.
- Librería y Cliente
  - [x] Selección de librería: Telethon (Python) por estabilidad y comunidad.
  - [x] Wrapper asíncrono con interface mínima: `connect()`, `disconnect()`, `send_message(chat_id,text)`, `on_event(handler)`.
  - [x] Manejo de login: flujo por código con endpoints temporales y expiración (administrado por el vendor; QR opcional a futuro).
- Backend API (FastAPI)
  - [x] Endpoints de administración por vendor:
    - [x] `POST /vendors/me/integrations/telegram/mtproto/session/init` (solicita login).
    - [x] `POST /vendors/me/integrations/telegram/mtproto/session/confirm` (acepta código/QR o session_string).
    - [x] `POST /vendors/me/integrations/telegram/mtproto/enable|disable` (enciende/apaga registro y estado).
    - [x] `GET /vendors/me/integrations/telegram/mtproto/status` (estado y métricas básicas).
  - [x] Feature flags y guardas:
    - [x] Reutilizar `_is_mtproto_allowed(vendor_id)` como gate principal.
    - [x] Kill switch global y por vendor.
- Orquestación y Runtime
  - [x] Supervisor de sesiones (scheduler/light service) que:
    - [x] Emita heartbeats y registre estado básico por vendor.
    - [x] Mantenga conexiones activas; reconecte con backoff exponencial.
    - [x] Limite concurrencia y respete ventanas de Telegram (flood‑wait).
  - [x] Hooks de eventos MTProto:
    - [x] Normalizar mensajes entrantes y rutear al grafo con el mismo contrato de Modo B.
- Seguridad y Cumplimiento
  - [x] Validaciones de uso aceptable por vendor (whitelist de chats/grupos).
  - [x] Rate limits básicos mediante FloodWaitError + logs para penalización futura.
  - [x] Registro de auditoría para altas/bajas de sesión, errores críticos y cambios de estado.
  - [x] Procedimiento de revocación de sesión (borrado de session_string y desconexión).
- Observabilidad
  - [x] Métricas prometheus/logs: `mtproto_sessions_active`, `mtproto_reconnects_total`, `mtproto_events_rate`, `mtproto_floodwait_seconds`.
  - [x] Dashboards por vendor con estado y últimos errores; alertas por reconexiones frecuentes y flood‑wait prolongado (base técnica lista en /metrics; dashboards se construyen en el stack de monitoreo).
- Frontend (Dashboard)
  - [x] UI para consentir Modo C (aceptación registrada).
  - [x] Habilitar/deshabilitar desde UI cuando exista sesión válida.
  - [x] Wizard de login MTProto (QR/código) con feedback de estado en tiempo real.
  - [x] Panel de estado: badges (healthy/degraded), último heartbeat, botón “Deshabilitar Modo C”.
- Integración con Grafo
  - [x] Uniformar canal `channel: "telegram_vendor_bot"` tanto para Bot API como para MTProto.
  - [x] Pruebas de enrutamiento de intents de ventas/inventario/soporte con mensajes MTProto.
- Pruebas y Calidad
  - [x] Tests unitarios para gates (`_is_mtproto_allowed`), transiciones de estado y serialización de sesión.
  - [x] Tests de integración stubbeando Telethon (simular mensajes entrantes y flood‑wait).
  - [x] Pruebas end‑to‑end en entorno de staging con vendors piloto, con checklist de reversión.
    - Checklist de reversión (staging):
      - Deshabilitar Modo C: `POST /vendors/me/integrations/telegram/mtproto/disable`
      - Revocar sesión MTProto: `POST /vendors/me/integrations/telegram/mtproto/revoke`
      - Verificar estado: `GET /vendors/me/integrations/telegram/mtproto/status` → `inactive` y `mtproto_enabled=false`
      - (Opcional) Suspender Bot API si aplica y registrar en AuditLog
      - Documentar el resultado y restaurar la configuración previa del vendor piloto
- Operación y Rollout
  - [x] Rollout progresivo: beta cerrada → enterprise → opt‑in por plan.
    - Admin endpoints para control dinámico:
      - GET `/telegram/admin/mtproto/state` → estado actual y overrides
      - POST `/telegram/admin/mtproto/kill-switch` `{ value: true|false }`
      - POST `/telegram/admin/mtproto/allowlist` `{ vendors: "1,42,7" }`
      - POST `/telegram/admin/mtproto/allowlist/add` `{ vendor_id: 42 }`
      - POST `/telegram/admin/mtproto/allowlist/remove` `{ vendor_id: 42 }`
    - Política de despliegue:
      - Beta cerrada: allowlist con vendors piloto
      - Enterprise: ampliar allowlist por cuenta
      - Opt‑in por plan: mantener allowlist por plan/comercial
  - [x] Playbook de incidentes MTProto (ban, flood‑wait prolongado, timeouts).
    - Ban/kill global: activar kill‑switch vía admin endpoint; revocar sesiones afectadas
    - Flood‑wait prolongado: monitorear métrica `mtproto_floodwait_seconds`; degradar a Bot API si persiste
    - Timeouts/conectividad: observar `mtproto_reconnects_total`; suspender temporalmente Modo C en vendors degradados

## 🤖 Fase 10.21: UX Auto‑creación de Bot Telegram
- Alcance
  - Diseñar la experiencia en Settings › Telegram para que el vendor pueda iniciar la auto‑creación de un bot sin interactuar manualmente con BotFather.
- Tareas
  - [x] Definir opción en Settings › Telegram para “Crear bot automáticamente” diferenciada de vinculación manual.
  - [x] Diseñar wizard:
    - [x] Paso 1: elegir nombre público del bot (ej. “Tienda Emace Assistant”).
    - [x] Paso 2: proponer username base (ej. `emace_<vendor_slug>_bot`) y permitir override simple.
  - [x] Definir estados de bot por vendor: `none`, `creating`, `ready`, `error`.
  - [x] Diseñar mensajes de UI para cada estado (creando, listo, error con causa legible).

## ⚙️ Fase 10.22: Orquestador BotFather vía MTProto
- Alcance
  - Implementar un orquestador backend que se comunique con `@BotFather` usando la sesión MTProto del vendor para crear bots de forma automatizada.
- Tareas
  - [x] Implementar componente `BotFatherOrchestrator` que:
    - Use la sesión MTProto del vendor para iniciar conversación con `@BotFather`.
    - Ejecute la máquina de estados `/newbot` → nombre → username → token, con timeouts y reintentos.
    - Reconozca y maneje errores típicos (username en uso, límites de creación, restricciones de BotFather).
  - [x] Persistir estado de creación:
    - Tabla o campos dedicados (por ejemplo `bot_creation_state`, `bot_creation_metadata`) por vendor.
    - Estados: `idle`, `sent_newbot`, `sent_name`, `sent_username`, `waiting_token`, `completed`, `failed`.
  - [x] Integrar con el handler MTProto:
    - Identificar `chat_id` de BotFather y enrutar sus mensajes al orquestador, no al grafo de negocio.

## 🔐 Fase 10.23: Persistencia y Seguridad de Credenciales de Bot
- Alcance
  - Guardar de forma segura el username y token del bot creado, configurando el webhook y vinculando el bot al vendor.
- Tareas
  - [x] Reutilizar `VendorTelegramIntegration` para almacenar:
    - [x] `bot_username`, `bot_token_encrypted`, `webhook_secret`, `is_active` (notado como `autocreated` a nivel de auditoría).
  - [x] Al obtener el token desde BotFather:
    - [x] Validar con `getMe` de la Bot API para confirmar validez y username.
    - [x] Cifrar token con las utilidades existentes antes de persistirlo.
    - [x] Generar `webhook_secret` aleatorio y configurar webhook en Telegram apuntando al endpoint multi‑tenant (si `TELEGRAM_PUBLIC_BASE_URL` está definido).

## 🛰️ Fase 10.24: API y Flujos de Control de Auto‑creación
- Alcance
  - Exponer endpoints y flujos de control para iniciar, monitorear y opcionalmente recrear bots automatizados.
- Tareas
  - [x] Añadir endpoints por vendor:
    - [x] `POST /vendors/me/integrations/telegram/bot/auto-create`
      - Body: `{ bot_name, username_hint }`.
      - Precondiciones: vendor con sesión MTProto `enabled` y sin creación en progreso.
      - Efecto: iniciar orquestador BotFather y dejar estado en `creating`.
    - [x] `GET /vendors/me/integrations/telegram/bot/status`
      - Devuelve `bot_status`, `bot_username`, `last_error` y metadatos relevantes (timestamps).
    - Opcional: `POST /vendors/me/integrations/telegram/bot/recreate` con confirmación explícita.
  - [x] Integrar con Settings › Telegram:
    - [x] Botón “Crear bot automáticamente” que dispara el `POST` y muestra progreso.
    - [x] Polling sobre `/bot/status` hasta `ready` o `error`.
    - [x] Mostrar username y estado del bot una vez creado.

## 🛡️ Fase 10.25: Límites, Legal y Operación de Bots Autocreados
- Alcance
  - Definir límites de uso, consideraciones legales y controles operacionales para la auto‑creación de bots.
- Tareas
  - [x] Definir límites:
    - [x] Máximo 1 bot autogenerado por vendor (v1) — bloqueo en endpoint de auto‑create si ya hay integración activa.
    - [x] Rate‑limit de creación por vendor/día y límite global — validación vía AuditLog; límites configurables en settings.
  - [x] Revisar términos de Telegram / BotFather y documentar:
    - [x] Consentimiento implícito al iniciar auto‑create; trazabilidad en AuditLog.
    - [x] Fallback operativo: suspender integración y/o forzar flujo manual si hay abuso/bloqueo.
  - [x] Integrar con administración:
    - [x] Panel admin de integraciones existente lista bots y estado.
    - [x] Acción admin para desactivar integración (suspender + quitar webhook) ya disponible.

## 📊 Fase 10.26: Observabilidad, Testing y Rollout de Auto‑creación
- Alcance
  - Asegurar que la auto‑creación de bots sea observable, testeable y desplegada de forma controlada.
- Tareas
  - [x] Métricas Prometheus:
    - [x] `mtproto_bot_autocreate_total{status="success|error"}`.
    - [x] Distribución de duración de creación por vendor (`mtproto_bot_autocreate_duration_seconds`).
  - [x] Logs estructurados de cada transición de estado en el orquestador (AuditLog `bot_auto_create_state`).
  - [x] Tests:
    - [x] Unit: máquina de estados del orquestador y parsers básicos de username/token.
    - Integración: uso de Telethon stub/fake que simule conversación con BotFather.
    - E2E: escenario completo “vendor sin bot → auto‑create → bot listo y webhook funcionando”.
  - [x] Rollout:
    - [x] Meter observabilidad en `/metrics` ya expuesto y endpoint `metrics-admin` para monitoreo.

## 🧩 Fase 10.27: Modelo y Estados de Integración de Bot
- Alcance
  - Extender el modelo de integración de Telegram para representar claramente el ciclo de vida del bot (activo, pausado, eliminado lógico) por vendor.
- Tareas
  - Backend
    - [x] Definir estados adicionales en `VendorTelegramIntegration` o modelo asociado (ej. `active`, `paused`, `deleted_logical`) y su semántica.
    - [x] Añadir migraciones necesarias para persistir estos estados y campos de metadatos (p. ej. `paused_at`, `deleted_at`, `paused_by_user_id`).
    - [x] Actualizar consultas y repositorios para filtrar correctamente por estado (por ejemplo, excluir bots eliminados lógicamente de listados activos).

## 🧩 Fase 10.28: API de Gestión de Bot del Vendor (Pausar, Reanudar, Editar, Eliminar)
- Alcance
  - Exponer endpoints de control para que cada vendor pueda pausar, reanudar, editar propiedades y eliminar su bot vinculado, con efectos consistentes en la capa de entrega.
- Tareas
  - Backend
    - [x] Implementar endpoints por vendor:
      - [x] `POST /vendors/me/integrations/telegram/bot/pause` → marca el bot como pausado y deshabilita el procesamiento de mensajes (desactiva webhook si aplica).
      - [x] `POST /vendors/me/integrations/telegram/bot/resume` → vuelve a activar el bot (restaura webhook y estado `active`).
      - [x] `PATCH /vendors/me/integrations/telegram/bot` → permite editar propiedades de la integración (regenerar `webhook_secret`); sin intentar cambiar el username de Telegram.
      - [x] `DELETE /vendors/me/integrations/telegram/bot` → elimina lógicamente la integración, desactiva el webhook y deja el estado en “deleted/archived”.
    - [x] Ajustar enrutamiento del grafo y capas de entrega para que bots en estado `paused` o `deleted` no reciban tráfico; devolver errores controlados al frontend.
    - [x] Registrar en `AuditLog` todas las acciones: `bot_paused`, `bot_resumed`, `bot_properties_updated`, `bot_deleted`, incluyendo `user_id`, `vendor_id` y metadatos relevantes.

## 🧩 Fase 10.29: UX de Gestión de Bot en Settings › Telegram
- Alcance
  - Incorporar en el dashboard de Settings › Telegram controles claros y seguros para que el vendor gestione el estado de su bot (pausa, reanudación, edición y eliminación).
- Tareas
  - Frontend (Settings › Telegram)
    - [ ] Añadir controles en el panel de estado del bot para:
      - [x] Pausar bot (con explicación clara del impacto en las conversaciones).
      - [x] Reanudar bot (indicando que vuelve a aceptar tráfico).
      - [ ] Editar propiedades visibles (alias amigable, descripción interna, flags como “solo soporte”, etc.).
      - [x] Eliminar bot/integración con doble confirmación y resumen del efecto (se corta el webhook y deja de responder).
      - [x] Regenerar secreto de webhook desde la UI (alineado con el PATCH de 10.28).
    - [x] Reflejar en la UI el estado actual del bot (`activo`, `pausado`, `eliminado`) y bloquear acciones incompatibles (p. ej. no permitir pause sobre un bot ya eliminado).
    - [x] Integrar feedback de errores y advertencias (por ejemplo, mensajes cuando el bot está pausado o eliminado y no recibirá mensajes).

## 🧩 Fase 10.30: Operación, Permisos y Políticas de Gestión de Bots
- Alcance
  - Definir las reglas operativas, permisos y lineamientos de retención para las acciones sobre bots del vendor, alineadas con seguridad y cumplimiento.
- Tareas
  - Operación y Políticas
    - [x] Definir reglas de permisos (RBAC) para quién puede pausar, reanudar, editar propiedades o eliminar bots (p. ej. solo `VENDOR_OWNER` o `TELEGRAM_ADMIN`).
    - [x] Documentar en el playbook de operación cómo usar la pausa/reanudación en casos de incidentes, abuso o mantenimiento.
    - [x] Alinear el comportamiento de eliminación con retención de datos: conservar historiales necesarios para auditoría, pero evitar nuevas interacciones a través del bot eliminado.

---

Implementación de una interfaz de usuario profesional con Next.js App Router, diseño distintivo y experiencia de usuario excepcional que evita las estéticas genéricas de IA.

NOTA: la web no va a estar habilitada para customer
### 11.1 Arquitectura Frontend Enterprise ✅
- [x] **Next.js 15+ con App Router**: Aprovechar Server Components, Streaming SSR y Suspense boundaries.
- [x] **TypeScript Estricto**: Type safety completo con tipos generados desde el backend.
- [x] **Tailwind CSS + PostCSS**: Sistema de diseño tokenizado con CSS variables para consistencia.
- [x] **Estructura Modular**: Organización por dominios funcionales (auth, dashboard, agents, settings).

### 11.2 Sistema de Diseño Único y Distintivo ✅
- [x] **Dirección Estética Bold**: Elegir un concepto extremo (brutalista, retro-futurista, orgánico, luxury/playful) y ejecutarlo con precisión. (Dark Industrial / Cyber-Enterprise implementado).
- [x] **Tipografía Característica**: Fuentes distintivas que eviten las genéricas (Inter, Roboto) - optar por choices con personalidad. (Syne y JetBrains Mono).
- [x] **Paleta de Color Cohesiva**: Colores dominantes con acentos afilados, evitando esquemas tímidos y distribuciones equitativas.
- [x] **Sistema de Espaciado**: Grid system personalizado con proporciones áureas o ratios inusuales para composiciones memorables.

### 11.3 Autenticación y Gestión de Sesión ✅
- [x] **Auth Flow Completo**: Registro, login, logout con estética industrial y validación.
- [x] **JWT Token Management**: Almacenamiento en cookies, middleware de protección de rutas.
- [x] **Protected Routes**: Middleware de autenticación con redirección automática.
- [x] **Multi-Rol UI**: Base para interfaces adaptativas según rol.

### 11.4 Dashboard Interactivo Multi-Agente ✅
- [x] **Shell Industrial**: Sidebar y TopBar con estética Dark Industrial.
- [x] **Vista de Agentes**: Grid dinámico con estado de agentes y métricas en tiempo real.
- [x] **Real-time Activity Feed**: Feed de actividad reciente con logs de sistema.
- [x] **Chat Interface Universal**: Terminal de comunicación flotante con selección de agentes y estética industrial.

### 11.5 Centro de Control y Métricas (Analytics) ✅
- [x] **Métricas de Rendimiento de Agentes**: Visualización de latencia, éxito de tareas y uso de herramientas.
- [x] **Estadísticas de Inventario**: Gráficos de niveles de stock, valor de activos y rotación.
- [x] **Logs de Actividad Crítica**: Historial detallado de operaciones realizadas por agentes y usuarios.
- [x] **Dashboards de Negocio**: Resumen de ventas, facturación y actividad de clientes.
- [x] **Analytics Dashboard**: Gráficos de rendimiento personalizados (SVG) integrados en el dashboard.

### 11.6 Gestión de Inventario y Catálogo (Frontend) ✅
- [x] **CRUD Visual**: Interfaces de alta calidad para crear, editar y gestionar productos con drag-and-drop de imágenes. (Rediseño industrial completado).
- [x] **Búsqueda Híbrida**: Búsqueda instantánea que combina texto y semántica con resultados en tiempo real.
- [x] **Bulk Operations**: Acciones masivas con selección múltiple y confirmaciones elegantes. (Implementado en InventoryList).
- [x] **Stock Alerts**: Notificaciones visuales para stock bajo con acciones rápidas de reabastecimiento.

### 11.7 Sistema de Notificaciones Enterprise ✅
- [x] **Toast Notifications**: Sistema de notificaciones industrial con differentes niveles (info, success, warning, error) y animaciones.
- [x] **Email Templates**: Previsualización y edición de plantillas de email con editor WYSIWYG.
- [x] **Push Notifications**: Notificaciones push del navegador para eventos críticos del negocio, con control desde Dashboard.
- [x] **Notification Center**: Panel centralizado con historial de notificaciones y acciones pendientes.

### 11.8 Performance y Optimización ✅
- [x] **Code Splitting**: Dynamic import de módulos pesados (ChatInterface, InventoryList) y Suspense.
- [x] **Caching Strategy**: Revalidación del Dashboard (SSR) cada 60s y fetch controlado por ruta.
- [x] **Image Optimization**: Next/Image con dominio remoto permitido y placeholder blur en Home.
- [x] **Bundle Analysis**: Configurado @next/bundle-analyzer con script `analyze` para inspección del bundle.

### 11.9 Accesibilidad y Responsive Design ✅
- [x] **WCAG 2.1 AA**: Focus visible global, aria-labels en TopBar y layout principal, y skip link a contenido.
- [x] **Responsive Completo**: Ajuste de tamaños en imágenes (sizes) y contenedores con id para navegación.
- [x] **Dark/Light Mode**: Toggle persistente con localStorage y variables CSS mediante `data-theme`.
- [x] **Internationalización (i18n)**: Configuración es/en en Next config y selector en TopBar.

### 11.10 Testing y Calidad ✅
- [x] **Unit Testing**: Vitest + React Testing Library para componentes críticos (InventoryList, TopBar, Notifications) y utilidades.
- [x] **E2E Testing**: Playwright para flujos completos de usuario (home, auth flujos base).
- [x] **Visual Regression**: Configurado en Playwright mediante snapshots (ejemplo en home).
- [x] **Performance Monitoring**: Real User Monitoring (RUM) implementado con `reportWebVitals` y componente `WebPerformance`.

### 11.11 Integración con Backend y Agentes ✅
- [x] **Type-Safe API Client**: Generación automática de tipos y clientes desde OpenAPI/Swagger del backend.
- [x] **Real-time Agent Communication**: WebSocket connection para comunicación bidireccional con agentes.
- [x] **Error Boundary Recovery**: Manejo elegante de errores con fallback UI y recuperación automática mediante `error.tsx` y `global-error.tsx`.
- [x] **Offline Support**: Funcionalidad básica offline con Service Workers y sincronización de datos.

### 11.12 Gestión de Conocimiento e Ingesta de Datos (Admin Capability)
- [x] **Backend: Endpoints de Ingesta Documental**: Crear rutas para subir PDFs/MDs/TXTs y procesarlos hacia Qdrant con aislamiento por `user_id`.
- [x] **Backend: Importación Masiva SQL**: Desarrollar lógica para carga masiva de productos (CSV/JSON) validando esquemas y propiedad de inquilino. (Implementado vía `KnowledgeManager` y `IngestionService`).
- [x] **Frontend: Panel de Base de Conocimiento**: Interfaz para visualizar, subir y eliminar documentos de la memoria semántica del agente.
- [x] **Frontend: Herramientas de Importación**: Wizard de importación de datos con previsualización y mapeo de campos para la base de datos relacional. (Integrado en el Dashboard de Conocimiento).
- [x] **RBAC Enforcement**: Asegurar que solo roles con permisos `KNOWLEDGE_ADMIN` (admin/vendor) puedan acceder a estas funciones.

### 11.13 Importación Masiva de Catálogo (Especializada) 📦 ✅
- [x] **Backend: Motor de Ingesta SQL (Products)**:
    - [x] Endpoint `POST /inventory/import` para procesar archivos `.csv` y `.xlsx`.
    - [x] Lógica de validación de esquema (nombre, SKU, precio, stock) y mapeo automático de campos.
    - [x] Procesamiento por lotes (batch processing) para evitar timeouts en catálogos grandes.
- [x] **Frontend: Interfaz de Importación de Productos**:
    - [x] Componente `ProductImportWizard` (BulkUpload) con zona de drag-and-drop.
    - [x] Tabla de previsualización de datos antes de confirmar la carga definitiva (Dry-run).
    - [x] Sistema de resolución de conflictos (omitir duplicados o actualizar existentes).
- [x] **Data Sanitization**: Limpieza automática de precios (monedas/decimales) y normalización de SKUs. (Implementado en el flujo de importación).

---

## 🏗️ Fase 12: Refactorización Visual "Industrial Command Center" (UI/UX Elite)
Transformación de la interfaz para proyectar una estética de centro de control crítico, sofisticado y proactivo.

### 12.1 Fundamentos Visuales y Estética
- [x] **Configuración de Temas (Tailwind v4)**:
    - [x] **Paleta de Colores**: Fondo en `Steel Gray` y `Midnight Blue` profundo. Acentos en `Safety Orange` (#FF5F1F) para alertas y `Cyber Lime` para estados activos.
    - [x] **Efectos Glassmorphism**: Implementar utilidades de `backdrop-blur(20px)` con bordes de 1px usando gradientes lineales sutiles (blanco 10% a transparente).
    - [x] **Texturas**: Aplicar un ruido (grain) sutil global mediante filtros SVG o capas de ruido CSS para la sensación industrial.
- [x] **Tipografía Técnica**:
    - [x] **Display**: Configurar `Aeonik` o `FK Grotesk` (se usó `Inter` como alternativa de alta calidad disponible) para encabezados y elementos de UI de alto impacto.
    - [x] **Monospace**: Integrar `JetBrains Mono` para todos los logs de agentes, terminales y datos técnicos.

### 12.2 Componentes de "Operador"
- [x] **Dashboard Command Center**:
    - [x] Rediseño de la cuadrícula de agentes con micro-animaciones de "escaneo" y estados de pulso.
    - [x] Implementación de "Mini-maps" de estado del sistema (Analytics Chart refactorizado).
- [x] **Chat Terminal Refinado**:
    - [x] Interfaz de chat que simula una consola de comando con tipografía mono y efectos de teletipo (refactorizado en ChatInterface).
    - [x] Indicadores visuales proactivos (Cyber Lime / Safety Orange) para estados de agentes y alertas.
- [x] **Glass Panels & Layout**:
    - [x] Refactorizar todos los contenedores a paneles de cristal refinado con sombras proyectadas profundas (clases `panel-industrial` actualizadas).
    - [x] Sidebar colapsable con estética militar/industrial y terminal text.

### 12.3 Micro-interacciones y Feedback
- [x] **Estados de Agentes**: Animaciones de carga que no sean genéricas (ej: barras de progreso segmentadas, escáneres circulares).
- [x] **Sonidos de Sistema (Opcional/Sutil)**: Implementar feedbacks auditivos casi imperceptibles para acciones críticas de confirmación.
- [x] **Transiciones Framer Motion**: Movimientos mecánicos y precisos (snappy) en lugar de transiciones suaves tradicionales.

### 12.4 Conciencia de Rol y RBAC Dinámico (Agente Operador) 🚀
- [x] **Arquitectura de Inyección de Metadatos**:
    - [x] Extender `SupervisorState` en `app/core/state.py` para incluir `user_info` (rol, nombre, permisos).
    - [x] Modificar controladores de Chat (HTTP/WS) para inyectar datos del usuario autenticado en el estado inicial del grafo.
- [x] **Prompt Engineering Contextual**:
    - [x] Refactorizar `SUPERVISOR_SYSTEM_PROMPT` para incluir sección de "Conciencia de Rol" con variables dinámicas.
    - [x] Ajustar prompts de especialistas (`CustomerSupport`) para adaptar su lenguaje según el interlocutor (vendedor vs cliente).
- [x] **Enforcement de Permisos en Grafo**:
    - [x] Implementar filtrado dinámico de `available_members` en el Supervisor basado en el rol del usuario inyectado.
    - [x] Asegurar que el ruteo hacia herramientas críticas (Inventory Write) esté restringido a nivel de grafo para el rol `customer`.
- [ ] **Auditoría de Roles en Logs**:
    - [ ] Mostrar visualmente en la terminal de chat el rol detectado del operador para transparencia del sistema.
    - [ ] Registrar en `ChatHistory` el rol con el que se generó cada interacción para análisis post-operativo.

---

## 🔐 Fase 13: Sistema de Gestión de Identidad y Acceso (IAM - Identity & Access Management)
Implementación de un sistema robusto que permita a los Vendedores (Vendors) crear y gestionar sus propios usuarios limitados con permisos granulares, similar a AWS IAM.

### 13.1 Modelo de Datos y Arquitectura IAM
- [x] **Estructura de Multi-Tenancy para Usuarios**:
    - [x] Modificar modelo `User` para incluir `parent_id` (auto-referencia) para identificar usuarios creados por un Vendor.
    - [x] Implementar el concepto de "Account Owner" (Vendor principal) y "IAM User" (Usuario limitado), donde los usuarios limitados siempre están ligados a su `parent_id` (Vendor).
    - [x] Incluir en los tokens (JWT) los claims `user_type` (`vendor` | `iam_user`) y `vendor_parent_id` para derivar el contexto de tenant sin credenciales adicionales.
- [x] **Políticas y Permisos Granulares**:
    - [x] Definir un esquema de permisos basado en acciones y recursos (ej: `inventory:write`, `knowledge:ingest`, `billing:view`).
    - [x] Crear modelo `IAMPolicy` para agrupar permisos en objetos reutilizables.
- [x] **Asignación de Políticas**:
    - [x] Relación muchos-a-muchos entre `User` y `IAMPolicy`.
    - [x] Soporte para "Permisos Heredados" del rol y "Permisos Explícitos" de políticas IAM (diseño; enforcement en Fase 13.2).

### 13.2 Backend IAM Core
- [x] **Flujo de Autenticación Particionado**:
    - [x] Exponer modalidad `login_iam` para usuarios limitados (endpoint dedicado).
    - [x] En `login_iam`, requerir `vendor_identifier` (email del vendor) y validar que el usuario pertenece a ese vendor (`parent_id`).
    - [x] Propagar `user_type=iam_user` y `vendor_parent_id` en el JWT al autenticar.
- [x] **API de Gestión de Usuarios IAM**:
    - [x] `POST /iam/users`: Crear usuario limitado asociado al Vendor actual.
    - [x] `GET /iam/users`: Listar usuarios del equipo del Vendor.
    - [x] `PATCH /iam/users/{id}/policies`: Asignar/Remover políticas a un usuario.
- [x] **Middleware de Autorización Avanzada**:
    - [x] Refactorizar `RoleChecker` para validar rol + políticas IAM activas.
    - [x] Implementar caché de permisos con TTL en memoria y hooks de invalidación (preparado para migrar a Redis).

### 13.3 Interfaz de Usuario (IAM Dashboard)
- [x] **Panel de Gestión de Equipo**:
    - [x] Vista de lista de usuarios con estados, roles y últimas conexiones.
    - [x] Formulario de creación de usuario con generador de contraseñas temporales.
- [x] **Editor de Políticas**:
    - [x] Interfaz visual para seleccionar permisos mediante checkboxes categorizados (Inventario, Clientes, Chat, etc.).
    - [x] Resumen visual de capacidades del usuario ("Access Summary").

### 13.4 Seguridad y Auditoría IAM
- [x] **Aislamiento de Datos (IAM Scoping)**:
    - [x] Garantizar que un usuario IAM solo pueda acceder a los datos (`user_id`) de su Vendor padre, derivado del claim `vendor_parent_id` del token.
- [x] **Logs de Auditoría IAM**:
    - [x] Registrar quién creó/modificó a quién y qué permisos fueron alterados.
- [x] **Restricción de Sesiones**:
    - [x] Capacidad del Vendor para revocar sesiones activas de sus usuarios limitados.

### 13.5 Autenticación (UX) con Opciones de Inicio de Sesión
- [x] **UI con dos opciones en Login**:
    - [x] Pestañas o botones: "Usuarios" (Vendor/administrador) y "Usuarios limitados".
    - [x] En "Usuarios limitados", agregar campo adicional `Vendor` (slug o email del Vendor) para ligar el inicio de sesión al Vendor correspondiente sin requerir múltiples credenciales de Vendors.
- [x] **Contexto de Tenant Automático**:
    - [x] Tras login exitoso, propagar `vendor_parent_id` al contexto de la app para filtrar datos y capacidades.

---

## 💳 Fase 14: Billing y Acceso (Mercado Pago)
Implementación del modelo de acceso y cobro basado en el documento de referencia [emace_billing_model.md](./emace_billing_model.md). El acceso al sistema se rige por un único estado `ACCESS_MODE = subscription | lifetime` con prioridad de `lifetime` sobre cualquier suscripción.

### 14.1 Modelo y Migraciones
- [x] **Entidad `vendor_access_state`**:
  - [x] Campos: `vendor_id` (unique), `access_mode` (`subscription` | `lifetime`), `source` (`trial` | `paid_subscription` | `lifetime_purchase`), `valid_until` (NULL para lifetime), `subscription_id_mp` (nullable), timestamps.
  - [x] Índices y restricciones: unique por `vendor_id`, índice por `valid_until` para barridos del scheduler.
  - [x] Migración inicial: crear estado `trial` en alta de cuenta (`valid_until = now + 30 días`).
- [x] **Eventos y Auditoría**:
  - [x] Tabla `billing_events` para persistir webhooks (raw + normalized) e idempotencia.
  - [x] Auditoría de cambios en `vendor_access_state` (quién/qué/cuándo).

### 14.2 Integración con Mercado Pago
- [x] **Configuración**:
  - [x] Variables de entorno: `MP_ACCESS_TOKEN`, `MP_WEBHOOK_SECRET`, `MP_WEBHOOK_URL`.
  - [x] Cliente/SDK con timeouts, reintentos y backoff.
- [x] **Suscripciones**:
  - [x] Endpoint `POST /billing/subscriptions` (crear suscripción) → retorna link de checkout (placeholder operativo).
  - [x] Webhook `POST /billing/webhooks/mp`:
    - [x] Pago aprobado: extender `valid_until` y setear `source = paid_subscription`.
    - [x] Pago fallido: marcar `past_due`; el scheduler decide suspensión.
- [x] **Lifetime**:
  - [x] Endpoint `POST /billing/lifetime` (compra única).
  - [x] Regla crítica: al confirmar lifetime → cancelar suscripción activa (si existe), limpiar `subscription_id_mp`, setear `access_mode = lifetime` e ignorar eventos posteriores de suscripción.
- [x] **Idempotencia y Seguridad**:
  - [x] Verificación de firma HMAC del webhook.
  - [x] Idempotencia por `x-request-id`/`mp_event_id`.

### 14.3 Reglas de Negocio y Scheduler
- [x] **Principios**:
  - [x] `lifetime` domina siempre sobre `subscription`.
  - [x] `trial` no interactúa con Mercado Pago.
- [x] **Scheduler**:
  - [x] Job periódico: si `now >= valid_until` y `source == trial` → registrar `trial_expired` y disparar degradación en 14.4.
  - [x] Job de saneamiento: registrar pendientes de webhooks para reintento y verificación de salud de suscripciones.

### 14.4 API y Enforcement de Acceso
- [x] **Endpoints**:
  - [x] `GET /billing/access-state`: estado actual del vendor y fechas.
  - [x] `POST /billing/refresh`: fuerza sincronización con MP si es necesario.
  - [x] `POST /billing/cancel-subscription`: cancela suscripción (mantener acceso hasta `valid_until`).
- [x] **Enforcement**:
  - [x] Middleware global: adjunta `vendor_access_state` al contexto (request.state.vendor_access).
    - [x] Trial: acceso completo salvo premium (ver dependencia `require_access(premium=True)` lista para usar).
    - [x] Trial expirado / suscripción vencida: degradación disponible vía dependencia (aplicar en endpoints premium).
    - [x] Lifetime: acceso total sin renovaciones.

### 14.5 Frontend (Settings → Billing)
- [x] **UI de Planes**:
  - [x] Mostrar estado: `trial`, `subscription (active/past_due)`, `lifetime`, `valid_until`.
  - [x] CTA: “Suscribirme” (link a checkout), “Comprar Lifetime”.
  - [x] Contador de días restantes en trial y estado de renovación.
- [x] **Flujos**:
  - [x] Páginas de retorno `success`/`failure` tras checkout (query param en Settings → Billing).
  - [x] Manejo inicial de reintentos/errores vía toasts e idempotencia de backend.
- [x] **Contexto**:
  - [x] Cacheo de `access_state` en cliente con React Query y refresco on-demand.

### 14.6 Observabilidad y Auditoría
- [x] **Logs**:
  - [x] Trazas estructuradas de llamadas a MP (request/response, latencia, retries).
  - [x] Eventos de webhook y transiciones de estado.
- [x] **Métricas**:
  - [x] Panel en Analytics: tasa de conversión, trials activos/expirados, churn por past_due.

### 14.7 Testing y QA
- [x] **Unit Tests**:
  - [x] Reglas de `vendor_access_state` (trial → subscription → lifetime).
  - [x] Idempotencia de webhooks y verificación de firma.
- [x] **Integration/E2E**:
  - [x] Flujo de alta trial, checkout de suscripción, renovación, falla y suspensión controlada.
  - [x] Compra lifetime con cancelación automática de suscripción.
- [x] **Simuladores**:
  - [x] Scripts para re-jugar webhooks y validar transiciones.

### 14.8 Despliegue y Seguridad
- [x] **Infra**:
  - [x] Exponer webhook público y registrar URL en MP.
  - [x] Variables de entorno y secretos en el entorno de despliegue.
  - [x] Docker Compose carga backend/.env vía env_file para disponibilidad en contenedores.
- [x] **Cumplimiento**:
  - [x] No almacenar datos sensibles de tarjeta (solo IDs/tokens).
  - [x] Revisión de permisos del token de MP (mínimos necesarios).
