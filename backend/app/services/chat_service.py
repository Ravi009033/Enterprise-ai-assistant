from backend.app.core.llm import get_llm


def process_chat(question: str, session_id: str):

    llm = get_llm()

    response = llm.invoke(question)

    answer = response.content

    if isinstance(answer, list):
        answer = "\n".join(
            item.get("text", "")
            for item in answer
            if isinstance(item, dict) and item.get("type") == "text"
        )

    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("Gemini returned an empty response")

    return {
        "answer": answer,
        "session_id": session_id,
        "status": "success"
    }