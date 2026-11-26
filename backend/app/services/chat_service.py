
from backend.app.agents.graph import assistant_graph


def process_chat(
    question: str,
    session_id: str,
    history: list[dict] | None = None,
    employee_id: str = "",
    user_id: int = 0,
) -> dict:

    # Scope the conversation to the authenticated user.
    # This prevents different users from sharing LangGraph state.
    scoped_session_id = f"user:{user_id}:session:{session_id}"

    config = {
        "configurable": {
            "thread_id": scoped_session_id
        }
    }

    # Retrieve previous conversation state.
    previous_state = assistant_graph.get_state(config).values

    # Restore any pending leave request.
    pending_leave = previous_state.get("pending_leave")

    # Identify the user's confirmation response.
    user_response = question.strip().lower()

    if user_response in {"yes", "y", "confirm", "submit"}:
        confirmation = "yes"

    elif user_response in {"no", "n", "cancel"}:
        confirmation = "no"

    else:
        confirmation = "unknown"

    initial_state = {
        "question": question,
        "session_id": scoped_session_id,
        "history": history or [],
        "route": "",
        "rewritten_question": "",
        "context": "",
        "answer": "",
        "sources": [],
        "status": "processing",
        "employee_id": employee_id,
        "tool_action": "",
        "pending_leave": pending_leave,
        "confirmation": confirmation,
    }

    # Execute LangGraph workflow.
    result = assistant_graph.invoke(
        initial_state,
        config=config
    )

    print("Authenticated employee:", employee_id)
    print("Final route:", result["route"])
    print("Final status:", result["status"])

    return {
        "answer": result["answer"],
        "session_id": session_id,
        "status": result["status"],
        "sources": result["sources"]
    }
