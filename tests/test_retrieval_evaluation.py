
from backend.app.rag.retrieval import retrieve_relevant_documents


TEST_CASES = [
    {
        "question": "What are the cancellation rules for confirmed train tickets?",
        "expected_relevant": True
    },
    {
        "question": "What are the cancellation charges for waitlisted tickets?",
        "expected_relevant": True
    },
    {
        "question": "What happens if a train is cancelled?",
        "expected_relevant": True
    },
    {
        "question": "What is the weather in Delhi today?",
        "expected_relevant": False
    },
    {
        "question": "How can I apply for a passport?",
        "expected_relevant": False
    }
]


def evaluate_retrieval():
    correct = 0
    total = len(TEST_CASES)

    for test_case in TEST_CASES:
        question = test_case["question"]
        expected = test_case["expected_relevant"]

        documents = retrieve_relevant_documents(
            question=question,
            k=4,
            score_threshold=0.50
        )

        actual = len(documents) > 0

        passed = actual == expected

        if passed:
            correct += 1

        print("\nQuestion:", question)
        print("Expected relevant:", expected)
        print("Actually relevant:", actual)
        print("Result:", "PASS" if passed else "FAIL")
        print("-" * 60)

    accuracy = (correct / total) * 100

    print("\nRetrieval Evaluation Summary")
    print("Total tests:", total)
    print("Correct:", correct)
    print("Incorrect:", total - correct)
    print(f"Accuracy: {accuracy:.2f}%")


if __name__ == "__main__":
    evaluate_retrieval()
