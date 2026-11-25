
def process_chat(question: str, session_id: str):

    # Temporary response for testing
    answer = (
        f"You asked: {question}. "
        "I am your Enterprise AI Assistant. "
        "Gemini integration will be added next."
    )

    return {
        "answer": answer,
        "session_id": session_id,
        "status": "success"
    }
