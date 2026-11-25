
from backend.app.rag.retrieval import retrieve_relevant_documents

questions = [
    "What are the cancellation rules for confirmed train tickets?",
    "What is the weather in Delhi today?"
]

for question in questions:
    print("\nQuestion:", question)

    documents = retrieve_relevant_documents(
        question=question,
        k=4,
        score_threshold=0.50
    )

    for document in documents:
        print("Source:", document.metadata.get("source"))
        print("Page:", document.metadata.get("page"))
        print("Content:", document.page_content[:150])
        print("-" * 50)
