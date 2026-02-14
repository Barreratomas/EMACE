# 📐 Asignación de Modelos LLM para Ecosistema Multi-Agente Cognitivo Enterprise

Este documento describe la asignación recomendada de modelos LLM (vía OpenRouter) para cada componente del sistema multi-agente definido, optimizando **razonamiento, latencia, coste y riesgo operativo**.

---

## 🧠 Principio Rector

En un sistema multi-agente con **QA, memoria vectorial y herramientas reales**, no se busca un único modelo “perfecto”, sino:

- **Especialización cognitiva por rol**
- **Separación entre razonamiento, creatividad y validación**
- **Redundancia controlada** mediante QA y RAG

---

## 🧑‍✈️ Supervisor / Router (Orquestador)

**Rol**: Entender intención, mantener estado global y enrutar tareas.

**Requisitos clave**:
- Razonamiento estructurado
- Estabilidad en prompts largos
- Bajo nivel de creatividad
- Excelente manejo de contexto

### ✅ Modelo recomendado
**StepFun: Step 3.5 Flash**

**Justificación**:
- Razonamiento sólido y consistente
- Contexto de hasta 256K tokens
- Ideal para StateGraph (LangGraph)
- Muy eficiente en coste y latencia

**Alternativa**:
- Aurora Alpha (si la latencia extrema es prioritaria)

**No recomendado**:
- Pony Alpha / Trinity (demasiado creativos para routing)

---

## 🧾 Agente de Facturación

**Rol**: Consultas de pagos, facturas y disputas.

**Requisitos clave**:
- Precisión absoluta
- Cero alucinaciones
- Estricto seguimiento de tools SQL

### ✅ Modelo recomendado
**Aurora Alpha**

**Justificación**:
- Muy rápido
- Poco propenso a embellishment
- Excelente cumplimiento de instrucciones
- Ideal para respuestas basadas en datos reales

**Controles obligatorios**:
- RAG desde `lessons_learned`
- Revisión por QA

---

## 🧑‍💻 Agente Técnico

**Rol**: Diagnóstico, configuración y troubleshooting.

**Requisitos clave**:
- Razonamiento paso a paso
- Uso intensivo de RAG
- Capacidad de análisis técnico

### ✅ Modelo recomendado
**StepFun: Step 3.5 Flash**

**Justificación**:
- Excelente para diagnóstico lógico
- Muy estable con documentación larga
- Bajo riesgo de soluciones inventadas

**Alternativa**:
- Pony Alpha (si se requiere explicación más humana)

---

## 🛒 Agente de Ventas

**Rol**: Catálogo, recomendaciones y persuasión moderada.

**Requisitos clave**:
- Lenguaje natural
- Adaptación al usuario
- Persuasión sin mentir

### ✅ Modelo recomendado
**Pony Alpha**

**Justificación**:
- Buen equilibrio entre lógica y creatividad
- Excelente para explicar planes y productos
- Maneja bien prompts largos y contextuales

**Reglas obligatorias**:
1. RAG desde `lessons_learned`
2. Validación por QA antes de responder

---

## 🛡️ Agente de QA & Learning

**Rol**: Auditor cognitivo y generador de aprendizaje sistémico.

**Funciones**:
- Detectar alucinaciones
- Verificar consistencia con datos
- Extraer reglas abstractas

### ✅ Modelo recomendado
**StepFun: Step 3.5 Flash (modo crítico)**

**Justificación**:
- Muy fuerte en evaluación semántica
- Ideal para prompts de validación
- Excelente extracción de reglas tipo policy

**Complemento opcional**:
- LiquidAI LFM2.5-1.2B Thinking (segundo pase barato)

---

## 🧠 Memoria Vectorial / RAG Auxiliar

**Rol**: Resumen, clasificación y extracción factual.

### ✅ Modelo recomendado
**LiquidAI: LFM2.5-1.2B Thinking**

**Justificación**:
- Muy bajo coste
- Excelente para tareas no visibles al usuario
- Ideal para chunking y resúmenes fieles

---

## 📊 Mapa Resumen

| Componente | Modelo |
|----------|--------|
| Supervisor / Router | Step 3.5 Flash |
| Agente Facturación | Aurora Alpha |
| Agente Técnico | Step 3.5 Flash |
| Agente Ventas | Pony Alpha |
| QA & Learning | Step 3.5 Flash |
| Memoria / RAG | LiquidAI 1.2B Thinking |

---

## ⚠️ Riesgos y Mitigaciones

### 🔴 Modelos Alpha (Aurora, Pony)
**Riesgos**:
- Cambios de comportamiento
- Drift

**Mitigación**:
- QA obligatorio
- Canary routing (10–20% del tráfico)

---

### 🔴 Logging forzado por proveedor
**Riesgos**:
- Exposición de datos sensibles

**Mitigación**:
- Redacción previa de prompts
- Token masking
- No enviar PII cruda

---

## 🧠 Observación Final

El ciclo **QA → lessons_learned → RAG** convierte modelos buenos en **sistemas excelentes**.

Este enfoque prioriza **consistencia, aprendizaje continuo y control**, reduciendo la dependencia de un único modelo “SOTA”.

---

**Estado**: Recomendación lista para implementación en producción 🚀

