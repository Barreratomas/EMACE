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

---

## 🎨 Fase 11: Frontend Moderno con Next.js 15+ (Interfaz de Usuario Enterprise)
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

### 11.11 Gestión de Conocimiento e Ingesta de Datos (Admin Capability)
- [ ] **Backend: Endpoints de Ingesta Documental**: Crear rutas para subir PDFs/MDs/TXTs y procesarlos hacia Qdrant con aislamiento por `user_id`.
- [ ] **Backend: Importación Masiva SQL**: Desarrollar lógica para carga masiva de productos (CSV/JSON) validando esquemas y propiedad de inquilino.
- [ ] **Frontend: Panel de Base de Conocimiento**: Interfaz para visualizar, subir y eliminar documentos de la memoria semántica del agente.
- [ ] **Frontend: Herramientas de Importación**: Wizard de importación de datos con previsualización y mapeo de campos para la base de datos relacional.
- [ ] **RBAC Enforcement**: Asegurar que solo roles con permisos `KNOWLEDGE_ADMIN` puedan acceder a estas funciones.

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
