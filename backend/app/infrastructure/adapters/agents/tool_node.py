from typing import Dict, Any, List, Callable
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import ToolMessage
from app.application.state import SupervisorState

async def tool_node(state: SupervisorState, config: RunnableConfig, tools_map: Dict[str, Callable]):
    """
    Ejecuta las herramientas solicitadas y retorna ToolMessages.
    """
    requested_tools = state.get("tool_results", [])
    new_messages = []
    results_summary = []
    
    for tool_req in requested_tools:
        name = tool_req.get("name")
        args = tool_req.get("args", {})
        # Usamos el id de la tool_call si existe, o generamos uno
        tool_call_id = tool_req.get("id", f"call_{name}")
        
        if name in tools_map:
            print(f"🛠️ Ejecutando herramienta: {name} con args: {args}")
            try:
                tool_func = tools_map[name]
                if hasattr(tool_func, "ainvoke"):
                    result = await tool_func.ainvoke(args)
                else:
                    import asyncio
                    if asyncio.iscoroutinefunction(tool_func):
                        result = await tool_func(**args)
                    else:
                        result = tool_func(**args)
                
                output = str(result)
                new_messages.append(ToolMessage(content=output, tool_call_id=tool_call_id))
                results_summary.append({"name": name, "args": args, "result": output})
                
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                print(f"❌ {error_msg}")
                new_messages.append(ToolMessage(content=error_msg, tool_call_id=tool_call_id, status="error"))
                results_summary.append({"name": name, "args": args, "result": error_msg})
        else:
            error_msg = "Error: Herramienta no disponible"
            print(f"⚠️ {error_msg}")
            new_messages.append(ToolMessage(content=error_msg, tool_call_id=tool_call_id, status="error"))
            
    return {
        "messages": new_messages, 
        "tool_results": results_summary, 
        "next_step": "RESPONDER"
    }
