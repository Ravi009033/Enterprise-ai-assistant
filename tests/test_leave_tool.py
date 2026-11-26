
from backend.app.agents.graph import assistant_graph


def run_test():

    state = {
        "question": (
            "Apply for 2 days of leave because of personal work."
        ),
        "session_id": "leave-tool-test-001",
        "history": [],
        "employee_id": "EMP001",
        "route": "",
        "tool_action": "",
        "rewritten_question": "",
        "context": "",
        "answer": "",
        "sources": [],
        "status": "processing",
    }

    result = assistant_graph.invoke(
        state,
        config={
            "configurable": {
                "thread_id": "leave-tool-test-001"
            }
        },
    )

    print("\nSelected route:", result["route"])
    print("\nAnswer:", result["answer"])
    print("\nStatus:", result["status"])

    assert result["route"] == "tool"
    assert result["status"] == "success"
    assert "Request ID" in result["answer"]

    print("\nLeave tool integration test passed!")


if __name__ == "__main__":
    run_test()
