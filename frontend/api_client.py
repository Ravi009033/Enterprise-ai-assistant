
import requests

API_URL = "http://127.0.0.1:8000"


def login_user(username, password):

    response = requests.post(
        f"{API_URL}/api/auth/login",
        data={
            "username": username,
            "password": password
        },
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def logout_user(access_token):

    response = requests.post(
        f"{API_URL}/api/auth/logout",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def get_current_user(access_token):
    response = requests.get(
        f"{API_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30
    )
    response.raise_for_status()
    return response.json()



def send_message(question, session_id, access_token, history=None):

    payload = {
        "question": question,
        "session_id": session_id,
        "history": history or []
    }

    response = requests.post(
        f"{API_URL}/api/chat",
        json=payload,
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        timeout=120
    )

    response.raise_for_status()

    return response.json()



def transcribe_audio(audio_bytes, access_token):
    response = requests.post(
        f"{API_URL}/api/voice/transcribe",
        files={
            "file": (
                "recording.wav",
                audio_bytes,
                "audio/wav"
            )
        },
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        timeout=120
    )

    response.raise_for_status()

    return response.json()



def generate_speech(text, access_token):
    response = requests.post(
        f"{API_URL}/api/voice/speak",
        params={"text": text},
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        timeout=120
    )

    response.raise_for_status()

    return response.content

