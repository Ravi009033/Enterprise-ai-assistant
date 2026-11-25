from backend.app.core.llm import get_llm
from backend.app.rag.retrieval import retrieve_relevant_documents
from backend.app.rag.query_rewriter import rewrite_query


def process_chat(
    question: str,
    session_id: str,
    history: list[dict] | None = None
):
    
    history = history or []

    # 1. Rewrite the question using conversation history
    standalone_question = rewrite_query(
        question=question,
        history=history
    )

    print("Original question:", question)
    print("Rewritten question:", standalone_question)

    # 2. Retrieve documents using the rewritten question
    retrieved_docs = retrieve_relevant_documents(
        question=standalone_question,
        k=4,
        score_threshold=0.50
    )

    # 2. Handle the case where no documents are indexed
    if not retrieved_docs:
        return {
            "answer": (
                "I couldn't find relevant information in the "
                "uploaded documents to answer your question."
            ),
            "session_id": session_id,
            "status": "no_relevant_documents",
            "sources": []
        }

    # 3. Prepare context and source references
    
    context_parts = []
    sources = []

    source_labels = {}

    for document in retrieved_docs:
        filename = document.metadata.get(
            "source", "Unknown document"
        )

        page = document.metadata.get("page", "Unknown")

        source_key = (filename, page)

        # Assign a label only once per unique document page.
        if source_key not in source_labels:
            label = f"Source {len(source_labels) + 1}"
            source_labels[source_key] = label

            sources.append({
                "label": label,
                "filename": filename,
                "page": page
            })

        label = source_labels[source_key]

        # Every chunk from the same page uses the same label.
        context_parts.append(
            f"[{label}: {filename}, Page {page}]\n"
            f"{document.page_content}"
        )

    context = "\n\n".join(context_parts)


    # 4. Build the RAG prompt
    prompt = f"""
You are an Enterprise AI Assistant.

Answer the user's question using ONLY the supplied document context.

Instructions:
1. Do not invent facts or information.
2. If the answer is not present in the context, clearly say:
   "I couldn't find this information in the uploaded documents."
3. Give a clear and concise answer.
4. Cite supporting sources using their labels, such as [Source 1].
5. If sources disagree, explain the disagreement.


SOURCE CITATION RULES:

1. Answer using only the provided document context.
2. Cite supporting information using labels such as [Source 1].
3. Use only source labels that actually appear in the context.
4. Do not invent source labels or page numbers.
5. If the context does not contain the answer, clearly say so.
6. If multiple sources support an answer, cite all relevant sources.

DOCUMENT CONTEXT:

{context}

USER QUESTION:

{question}

ANSWER:
"""

    # 5. Generate the answer using Gemini
    llm = get_llm()

    response = llm.invoke(prompt)

    answer = response.content

    # 6. Extract text from Gemini response
    if isinstance(answer, list):
        answer = "\n".join(
            item.get("text", "")
            for item in answer
            if isinstance(item, dict)
            and item.get("type") == "text"
        )

    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("Gemini returned an empty response")

    # 7. Return answer and sources
    return {
        "answer": answer,
        "session_id": session_id,
        "status": "success",
        "sources": sources
    }