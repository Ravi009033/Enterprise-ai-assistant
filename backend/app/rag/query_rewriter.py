from backend.app.core.llm import get_llm


def rewrite_query(question: str, history: list[dict]) -> str:

    # No history means this is a standalone question
    if not history:
        return question

    # Prepare conversation history
    conversation = []

    for message in history[-10:]:
        role = message["role"]
        content = message["content"]

        conversation.append(
            f"{role.upper()}: {content}"
        )

    history_text = "\n".join(conversation)

    prompt = f"""
You are a query rewriting assistant.

Your task is to convert the latest user question into a
standalone question using the conversation history.

Rules:
1. Preserve the original meaning.
2. Resolve references such as "it", "that", "those" and "what about".
3. Do not answer the question.
4. Do not introduce new facts.
5. If the question is already standalone, keep it unchanged.
6. Return only the rewritten question.

CONVERSATION HISTORY:

{history_text}

LATEST USER QUESTION:

{question}

STANDALONE QUESTION:
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

    if not isinstance(content, str) or not content.strip():
        return question

    return content.strip()