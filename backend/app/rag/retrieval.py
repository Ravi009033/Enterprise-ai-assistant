
from langchain_core.documents import Document
from backend.app.rag.vector_store import get_vector_store


def retrieve_documents(
    question: str,
    k: int = 4
) -> list[Document]:

    vector_store = get_vector_store()

    return vector_store.similarity_search(
        query=question,
        k=k
    )


def retrieve_documents_with_scores(
    question: str,
    k: int = 4
) -> list[tuple[Document, float]]:

    vector_store = get_vector_store()

    results = vector_store.similarity_search_with_score(
        query=question,
        k=k
    )

    scored_documents = []

    for document, distance in results:
        similarity_score = 1 / (1 + distance)

        scored_documents.append(
            (document, similarity_score)
        )

    return scored_documents


def retrieve_relevant_documents(
    question: str,
    k: int = 4,
    score_threshold: float = 0.50
) -> list[Document]:

    results = retrieve_documents_with_scores(
        question=question,
        k=k
    )

    relevant_documents = []

    for document, score in results:
        print(
            f"Similarity score: {score:.4f} | "
            f"Threshold: {score_threshold}"
        )

        if score >= score_threshold:
            relevant_documents.append(document)

    print(
        f"Relevant documents: "
        f"{len(relevant_documents)}/{len(results)}"
    )

    return relevant_documents
