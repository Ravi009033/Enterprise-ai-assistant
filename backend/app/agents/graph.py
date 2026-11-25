
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from backend.app.agents.state import AssistantState
from backend.app.agents.nodes import (
    router_node,
    rag_node,
    general_node,
    tool_node,
)


def route_question(state: AssistantState) -> str:
    return state["route"]


def build_graph():
    workflow = StateGraph(AssistantState)

    workflow.add_node("router", router_node)
    workflow.add_node("rag", rag_node)
    workflow.add_node("general", general_node)
    workflow.add_node("tool", tool_node)

    workflow.add_edge(START, "router")

    workflow.add_conditional_edges(
        "router",
        route_question,
        {
            "rag": "rag",
            "general": "general",
            "tool": "tool",
        },
    )

    workflow.add_edge("rag", END)
    workflow.add_edge("general", END)
    workflow.add_edge("tool", END)

    # Store graph state separately for each conversation thread.
    memory = MemorySaver()

    return workflow.compile(checkpointer=memory)


assistant_graph = build_graph()
