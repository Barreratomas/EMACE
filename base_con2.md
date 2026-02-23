# Base de Conocimiento – Operación Comercial y Soporte IT

Documento interno utilizado por agentes conversacionales y personal de atención. Define reglas de respuesta, contexto de negocio y catálogo disponible.

---

## 1. Contexto del Negocio

- Tipo de negocio: Comercialización de tecnología y servicios IT
- Modelo de ventas: Venta directa + servicios recurrentes
- Perfil de clientes: Empresas, oficinas, profesionales, usuarios finales
- Objetivo del asistente: Resolver dudas, guiar compras y evitar errores de promesa

---

## 2. Reglas Generales para Agentes

- Priorizar claridad sobre tecnicismo
- No asumir especificaciones técnicas no confirmadas
- Nunca garantizar stock o precios sin validación implícita
- Siempre ofrecer alternativa ante limitaciones

---

## 3. Catálogo de Productos

### 3.1 Equipamiento (Hardware)

**Laptop HP**  
REF: 000001  
Tipo: Producto físico  
Precio de referencia: $1,200  
Stock actual: 15 unidades  
Estado: Activo  

**Comportamiento esperado del agente:**  
- Confirmar disponibilidad normal  
- Ofrecer accesorios o complementos si corresponde  

---

**Servidor Dell**  
REF: 000002  
Tipo: Producto físico  
Precio de referencia: $2,500  
Stock actual: 5 unidades  
Estado: Activo  

**Comportamiento esperado del agente:**  
- Advertir disponibilidad limitada  
- Recomendar verificación o reserva  

---

**Mouse Logitech**  
REF: 000006  
Tipo: Producto físico  
Precio de referencia: $25  
Stock actual: 100 unidades  
Estado: Activo  

**Comportamiento esperado del agente:**  
- Responder con alta confianza de disponibilidad  
- Sugerir compras por volumen si aplica  

---

**Teclado Mecánico**  
REF: 000007  
Tipo: Producto físico  
Precio de referencia: $80  
Stock actual: 30 unidades  
Estado: Archivado  

**Comportamiento esperado del agente:**  
- No ofrecer proactivamente  
- Solo responder si el cliente lo menciona  

---

### 3.2 Software

**Licencia Windows**  
REF: 000004  
Tipo: Licencia / Producto digital  
Precio de referencia: $150  
Stock actual: 50 unidades  
Estado: Activo  

**Comportamiento esperado del agente:**  
- Consultar versión o necesidad específica  
- Evitar suposiciones de compatibilidad  

---

### 3.3 Servicios

**Mantenimiento Mensual**  
REF: 000003  
Tipo: Servicio recurrente  
Precio de referencia: $300  
Disponibilidad: SLA activo  
Estado: Activo  

**Comportamiento esperado del agente:**  
- Presentar como servicio continuo  
- Enfatizar beneficios operativos  

---

**Consultoría Seguridad**  
REF: 000005  
Tipo: Servicio profesional  
Precio de referencia: $1,500  
Disponibilidad: SLA activo  
Estado: Pausado  

**Comportamiento esperado del agente:**  
- Indicar no disponible temporalmente  
- Ofrecer contacto o alternativa  

---

## 4. Gestión de Disponibilidad

| Estado      | Acción del Agente |
|------------|-------------------|
| Activo     | Puede ofrecerse normalmente |
| Stock bajo | Advertir limitación |
| Archivado  | No sugerir, solo responder |
| Pausado    | Informar indisponibilidad |

---

## 5. Manejo de Precios

- Todos los valores son informativos
- El agente debe evitar frases de confirmación absoluta
- Frases recomendadas:
  - "Precio de referencia"
  - "Valor estimado"
  - "Sujeto a confirmación"

---

## 6. Plantillas de Respuesta Recomendadas

**Consulta de stock:**  
"Actualmente contamos con disponibilidad. Si necesitás varias unidades, puedo ayudarte a verificar cantidades."

---

**Stock limitado:**  
"Quedan pocas unidades disponibles. Si querés, puedo ayudarte a gestionar una reserva."

---

**Producto archivado:**  
"Ese producto ya no forma parte del catálogo activo, pero puedo sugerirte alternativas similares."

---

**Servicio pausado:**  
"Por el momento ese servicio no se encuentra disponible. Si querés, puedo recomendarte otra opción."

---

## 7. Actualización del Documento

- Revisar ante cambios de inventario
- Sincronizar con la base de datos
- Evitar contradicciones con precios o estados reales
