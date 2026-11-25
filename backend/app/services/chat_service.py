
from backend.app.agents.graph import assistant_graph


def process_chat(
    question: str,
    session_id: str,
    history: list[dict] | None = None
) -> dict:

    initial_state = {
        "question": question,
        "session_id": session_id,
        "history": history or [],
        "route": "",
        "rewritten_question": "",
        "context": "",
        "answer": "",
        "sources": [],
        "status": "processing",
        "employee_id": "EMP001",
    }

    # Execute the LangGraph workflow
    result = assistant_graph.invoke(
        initial_state,
        config={
            "configurable": {
                "thread_id": session_id
            }
        }
    )

    print("Final route:", result["route"])
    print("Final status:", result["status"])

    return {
        "answer": result["answer"],
        "session_id": session_id,
        "status": result["status"],
        "sources": result["sources"]
    }
