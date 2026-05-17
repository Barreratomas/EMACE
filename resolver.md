Objetivo: Modernizar la arquitectura de agentes eliminando dependencias innecesarias del patrón ReAct y migrando a un workflow explícito con LangGraph.

Contexto del proyecto:
El sistema actual utiliza:

* LangChain Core (prompts, messages, runnables)
* LangGraph
* create_react_agent desde langgraph.prebuilt
* herramientas personalizadas en app/tools
* un sistema de RAG en app/core/rag/retriever
* un supervisor que coordina agentes
* Pydantic para validación

Problema actual:
El sistema depende de create_react_agent (patrón ReAct). Este patrón introduce loops de razonamiento, mayor consumo de tokens y menos control del flujo. Queremos migrar hacia una arquitectura moderna basada en workflows explícitos con LangGraph.

Objetivo de la refactorización:
Reemplazar agentes basados en create_react_agent por workflows explícitos usando StateGraph en LangGraph.

Requisitos de arquitectura:

1. Mantener:

* LangGraph como motor de orquestación
* LangChain Core solo para primitives (messages, prompts, runnables)
* Pydantic para modelos de estado
* Las tools existentes en app/tools
* El sistema RAG existente

2. Eliminar o reducir:

* Uso de create_react_agent
* Lógica de razonamiento basada en ReAct
* Loops implícitos de agente

3. Implementar un workflow explícito usando StateGraph.

Arquitectura objetivo:

User Input
↓
Router Node
↓
Tool Node (si se necesita tool)
↓
LLM Node
↓
Response Node

Tareas a realizar:

1. Crear un módulo de workflow de agentes basado en LangGraph:
   app/agents/workflow/

2. Definir un estado del agente usando Pydantic o TypedDict:

AgentState debe incluir:

* messages
* tool_results
* context (para RAG)
* next_step

3. Implementar nodos separados:

router_node:

* decide si se necesita una tool o respuesta directa

tool_node:

* ejecuta herramientas desde app/tools

rag_node:

* consulta app.core.rag.retriever cuando sea necesario

llm_node:

* genera respuesta final usando el modelo definido en app.core.llm

4. Construir el grafo con LangGraph:

* usar StateGraph
* definir nodos
* definir edges explícitos
* evitar loops implícitos

5. Mantener compatibilidad con:

* prompts existentes en app.core.prompts
* tools actuales
* supervisor si depende de los agentes

6. Documentar:

* nueva arquitectura
* flujo del grafo
* responsabilidades de cada nodo

Resultado esperado:

* eliminar dependencia de create_react_agent
* arquitectura basada en workflows explícitos
* mejor control del flujo del agente
* menos consumo de tokens
* mayor estabilidad en producción

Importante:

No eliminar LangChain Core. Solo evitar usar LangChain Agents o AgentExecutor. LangChain Core debe seguir usándose para prompts y mensajes.

