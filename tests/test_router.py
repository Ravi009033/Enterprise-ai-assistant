
from backend.app.agents.nodes import router_node


TEST_QUESTIONS = [
    "What are the cancellation rules for train tickets?",
    "Explain Python decorators with an example.",
    "What is my employee leave balance?",
    "What is the difference between SQL and NoSQL?",
    "What is the company attendance policy?"
]


for question in TEST_QUESTIONS:

    state = {
        "question": question
    }

    result = router_node(state)

    print("\nQuestion:", question)
    print("Route:", result["route"])
    print("-" * 50)
