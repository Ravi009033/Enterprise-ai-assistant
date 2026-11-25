import requests

API_URL = "http://127.0.0.1:8000"


def send_message(question, session_id, history=None):

    payload = {
        "question": question,
        "session_id": session_id,
        "history": history or []
    }

    response = requests.post(
        f"{API_URL}/api/chat",
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    return response.json()