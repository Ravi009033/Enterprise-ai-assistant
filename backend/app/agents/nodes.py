
from backend.app.core.llm import get_llm
from backend.app.rag.query_rewriter import rewrite_query
from backend.app.rag.retrieval import retrieve_relevant_documents
from backend.app.services.employee_service import get_leave_balance



def router_node(state: dict) -> dict:
    """
    Classifies the user's question into:
    rag, general, or tool.
    """

    question = state["question"]

    prompt = f"""
You are an intelligent enterprise assistant router.

Classify the user's question into exactly one category:

1. rag:
   Questions about company documents, uploaded PDFs,
   policies, procedures, rules, or internal knowledge.

2. general:
   General knowledge, programming, explanations,
   greetings, or normal conversation.

3. tool:
   Requests requiring an external enterprise system,
   such as employee leave balance, attendance records,
   payroll, database queries, or HR information.

Rules:
- Return only one word.
- Allowed outputs: rag, general, tool.
- Do not explain your decision.

User question:
{question}

Category:
"""

    llm = get_llm()

    response = llm.invoke(prompt)

    content = response.content

    if isinstance(content, list):
        content = "\n".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict)
            and item.get("type") == "text"
        )

    route = content.strip().lower()

    if route not in {"rag", "general", "tool"}:
        route = "general"

    print(f"User question: {question}")
    print(f"Selected route: {route}")

    return {
        "route": route
    }


def rag_node(state: dict) -> dict:
    question = state["question"]
    history = state.get("history", [])

    standalone_question = rewrite_query(
        question=question,
        history=history
    )

    print("RAG rewritten question:", standalone_question)

    documents = retrieve_relevant_documents(
        question=standalone_question,
        k=4,
        score_threshold=0.50
    )

    if not documents:
        return {
            "rewritten_question": standalone_question,
            "context": "",
            "answer": (
                "I couldn't find relevant information in "
                "the uploaded documents to answer your question."
            ),
            "sources": [],
            "status": "no_relevant_documents"
        }

    context_parts = []
    sources = []
    source_labels = {}

    for document in documents:
        filename = document.metadata.get(
            "source", "Unknown document"
        )
        page = document.metadata.get("page", "Unknown")

        source_key = (filename, page)

        if source_key not in source_labels:
            label = f"Source {len(source_labels) + 1}"
            source_labels[source_key] = label

            sources.append({
                "label": label,
                "filename": filename,
                "page": page
            })

        label = source_labels[source_key]

        context_parts.append(
            f"[{label}: {filename}, Page {page}]\n"
            f"{document.page_content}"
        )

    context = "\n\n".join(context_parts)

    prompt = f"""
You are an enterprise document assistant.

Answer the user's question using only the provided context.

Rules:
1. Do not invent facts.
2. Cite supporting information using [Source 1] format.
3. Use only source labels provided in the context.
4. If information is missing, say so clearly.

Context:
{context}

User question:
{question}

Answer:
"""

    response = get_llm().invoke(prompt)
    content = response.content

    if isinstance(content, list):
        content = "\n".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict)
            and item.get("type") == "text"
        )

    return {
        "rewritten_question": standalone_question,
        "context": context,
        "answer": content,
        "sources": sources,
        "status": "success"
    }


def general_node(state: dict) -> dict:
    question = state["question"]

    prompt = f"""
You are a helpful AI assistant.

Answer the user's question clearly and accurately.

Question:
{question}
"""

    response = get_llm().invoke(prompt)
    content = response.content

    if isinstance(content, list):
        content = "\n".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict)
            and item.get("type") == "text"
        )

    return {
        "answer": content,
        "sources": [],
        "status": "success"
    }


def tool_node(state: dict) -> dict:
    employee_id = state.get("employee_id")

    if not employee_id:
        return {
            "answer": "Employee identity is not configured.",
            "sources": [],
            "status": "identity_not_configured",
        }

    try:
        leave_data = get_leave_balance(employee_id)

        answer = (
            f"Hello {leave_data['employee_name']}! "
            f"Here is your leave balance:\n"
            f"- Total leaves: {leave_data['total_leaves']}\n"
            f"- Used leaves: {leave_data['used_leaves']}\n"
            f"- Remaining leaves: {leave_data['remaining_leaves']}"
        )

        return {
            "answer": answer,
            "sources": [],
            "status": "success",
        }

    except ValueError:
        return {
            "answer": "Unable to find your employee record.",
            "sources": [],
            "status": "employee_not_found",
        }
