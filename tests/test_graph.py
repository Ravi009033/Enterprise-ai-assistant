
from backend.app.agents.graph import assistant_graph


TEST_QUESTIONS = [
    "What are the cancellation rules for confirmed train tickets?",
    "Explain Python decorators with an example.",
    "What is my employee leave balance?"
]


for question in TEST_QUESTIONS:

    print("\nQuestion:", question)

    result = assistant_graph.invoke({
        "question": question,
        "session_id": "test-session",
        "history": [],
        "route": "",
        "rewritten_question": "",
        "context": "",
        "answer": "",
        "sources": [],
        "status": "processing"
    })

    print("Final route:", result["route"])
    print("Answer:", result["answer"])
    print("Status:", result["status"])
    print("Sources:", result["sources"])
    print("=" * 70)
