
import requests


API_URL = "http://127.0.0.1:8000"


def send_message(question, session_id):

    payload = {
        "question": question,
        "session_id": session_id
    }

    response = requests.post(
        f"{API_URL}/api/chat",
        json=payload,
        timeout=60
    )

    response.raise_for_status()

    return response.json()
