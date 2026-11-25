
from backend.app.agents.graph import assistant_graph


def test_employee_leave_balance():
    state = {
        "question": "What is my remaining leave balance?",
        "session_id": "employee-test-001",
        "history": [],
        "employee_id": "EMP001",
        "route": "",
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
                "thread_id": "employee-test-001"
            }
        },
    )

    print("\nSelected route:", result["route"])
    print("\nAnswer:", result["answer"])
    print("\nStatus:", result["status"])

    assert result["route"] == "tool"
    assert result["status"] == "success"
    assert "16" in result["answer"]


if __name__ == "__main__":
    test_employee_leave_balance()
    print("\nEmployee tool integration test passed!")
