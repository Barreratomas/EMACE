Objetivo: Modernizar la arquitectura de agentes eliminando dependencias innecesarias del patrón ReAct y migrando a un workflow explícito con LangGraph, integrado en la nueva Arquitectura Hexagonal.

ESTADO: ✅ COMPLETADO

Resumen de la refactorización:
Se ha reemplazado el uso de `create_react_agent` por un sistema de subgrafos explícitos para cada especialista. La orquestación reside en la capa de Application y los nodos en Infrastructure.

Tareas realizadas:

1. ✅ Reorganizar el módulo de workflow: Se creó `app/application/graph/specialist_factory.py` para centralizar la construcción de grafos.
2. ✅ Definir el estado: `SupervisorState` en `app/application/state.py` incluye ahora `tool_results`, `context` y `next_step`.
3. ✅ Implementar nodos como Adaptadores: Se crearon `router_node`, `tool_node`, `rag_node` y `llm_node` en `app/infrastructure/adapters/agents/`.
4. ✅ Construir el grafo con LangGraph: Se implementó la lógica condicional `should_continue` para control programático del flujo.
5. ✅ Mantener compatibilidad: Se actualizaron todos los especialistas (Tech, Sales, Inventory, Billing) manteniendo sus prompts y herramientas originales.
6. ✅ Documentar: Se actualizó `DISEÑO_DEL_SISTEMA.md` con la nueva arquitectura de subgrafos.

Arquitectura final implementada:

User Input (Interfaces)
↓
Orquestador / Supervisor (Application - workflow.py)
↓
Especialista (Subgrafo en Application - specialist_factory.py)
    ↳ RAG Node (Infrastructure)
    ↳ Router Node (Infrastructure)
    ↳ Tool Node (Infrastructure)
    ↳ Conditional Edge (Lógica Python)
    ↳ LLM Node (Infrastructure)
↓
QA Node (Infrastructure)
↓
Response Node (Application)

Beneficios obtenidos:
* Eliminación de loops implícitos de ReAct.
* Control total del flujo de los agentes.
* Ahorro de tokens mediante lógica condicional programática.
* Estricto cumplimiento de la Arquitectura Hexagonal.
