from uuid import uuid4

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from contextlib import asynccontextmanager
from backend.app.main import app
from backend.app.db.database import SessionLocal
from backend.app.models.employee import Employee
from backend.app.models.user import User
from backend.app.services.auth_service import create_user


client = TestClient(app)


class FakeDeepgramConnection:

    def __init__(self):
        self.audio_chunks = []
        self.finalized = False

    async def send_media(self, audio_chunk):
        self.audio_chunks.append(audio_chunk)

    async def send_finalize(self):
        self.finalized = True


fake_deepgram = FakeDeepgramConnection()


@asynccontextmanager
async def fake_live_transcription_session(websocket):
    yield fake_deepgram


def test_authenticated_websocket(monkeypatch):
    monkeypatch.setattr(
        "backend.app.api.websocket.live_transcription_session",
        fake_live_transcription_session,
    )

    fake_deepgram.audio_chunks.clear()
    fake_deepgram.finalized = False

    suffix = uuid4().hex[:8]
    employee_id = f"WS{suffix.upper()}"
    username = f"ws_employee_{suffix}"
    password = "SecurePassword123"

    db = SessionLocal()

    try:
        employee = Employee(
            employee_id=employee_id,
            name="WebSocket Test Employee",
            total_leaves=24,
            used_leaves=0,
        )

        db.add(employee)
        db.commit()

    finally:
        db.close()

    try:
        create_user(
            username=username,
            password=password,
            role="employee",
            employee_id=employee_id,
        )

        # Login and obtain JWT.
        login_response = client.post(
            "/api/auth/login",
            data={
                "username": username,
                "password": password,
            },
        )

        assert login_response.status_code == 200

        token = login_response.json()["access_token"]

        print("JWT token obtained successfully!")

        # Test 1: Reject connection without token.
        try:
            with client.websocket_connect("/ws/voice"):
                assert False, "Unauthenticated connection was accepted!"

        except WebSocketDisconnect as exc:
            assert exc.code == 1008

        print("Missing token rejection passed!")

        # Test 2: Reject invalid token.
        try:
            with client.websocket_connect(
                "/ws/voice?token=invalid.token.value"
            ):
                assert False, "Invalid token was accepted!"

        except WebSocketDisconnect as exc:
            assert exc.code == 1008

        print("Invalid token rejection passed!")

        # Test 3: Accept valid token.
        with client.websocket_connect(
            f"/ws/voice?token={token}"
        ) as websocket:

            
            response = websocket.receive_json()

            print("Connection response:", response)

            assert response["type"] == "connection"
            assert response["user_id"] > 0
            assert response["username"] == username

            # Wait for Deepgram readiness.
            response = websocket.receive_json()

            print("Deepgram response:", response)

            assert response["type"] == "transcription_ready"

            # Send binary audio.
            audio_chunk = bytes(32000)

            websocket.send_bytes(audio_chunk)

            # Stop audio streaming.
            websocket.send_text("stop")

            response = websocket.receive_json()

            print("Stop response:", response)

            assert response["type"] == "stream_stopped"

            assert fake_deepgram.audio_chunks == [audio_chunk]
            assert fake_deepgram.finalized is True

            print("Deepgram audio forwarding test passed!")



        print("Valid JWT WebSocket authentication passed!")

        print("\nAll WebSocket authentication tests passed!")

    finally:
        db = SessionLocal()

        try:
            db.query(User).filter(
                User.username == username
            ).delete(synchronize_session=False)

            db.query(Employee).filter(
                Employee.employee_id == employee_id
            ).delete(synchronize_session=False)

            db.commit()

            print("Temporary test data cleaned up!")

        finally:
            db.close()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-s"])