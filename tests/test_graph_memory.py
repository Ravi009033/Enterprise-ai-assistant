
from backend.app.agents.graph import assistant_graph


def run_test():
    session_id = "memory-test-session-001"

    first_state = {
        "question": "Explain Python in one sentence.",
        "session_id": session_id,
        "history": [],
        "route": "",
        "rewritten_question": "",
        "context": "",
        "answer": "",
        "sources": [],
        "status": "processing",
    }

    config = {
        "configurable": {
            "thread_id": session_id
        }
    }

    first_result = assistant_graph.invoke(
        first_state,
        config=config,
    )

    print("\nFirst response:")
    print(first_result["answer"])

    # Read the checkpoint saved for this conversation.
    checkpoint = assistant_graph.get_state(config)

    print("\nCheckpoint values:")
    print(checkpoint.values)

    assert checkpoint.values["answer"] == first_result["answer"]

    print("\nConversation checkpoint test passed!")


if __name__ == "__main__":
    run_test()
