
from backend.app.agents.graph import assistant_graph


def process_chat(
    question: str,
    session_id: str,
    history: list[dict] | None = None
) -> dict:


    # Create the LangGraph session configuration.
    config = {
        "configurable": {
            "thread_id": session_id
        }
    }

    # Retrieve the previous conversation state.
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
        "session_id": session_id,
        "history": history or [],
        "route": "",
        "rewritten_question": "",
        "context": "",
        "answer": "",
        "sources": [],
        "status": "processing",
        "employee_id": "EMP001",
        "tool_action": "",
        "pending_leave": pending_leave,
        "confirmation": confirmation,
    }

    # Execute the LangGraph workflow
    result = assistant_graph.invoke(
        initial_state,
        config=config
    )

    print("Final route:", result["route"])
    print("Final status:", result["status"])

    return {
        "answer": result["answer"],
        "session_id": session_id,
        "status": result["status"],
        "sources": result["sources"]
    }
