
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.core.dependencies import get_user_from_token
from backend.app.services.speech_service import (
    live_transcription_session,
    text_to_speech,
)
from backend.app.services.chat_service import process_chat
import asyncio
import uuid

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):

    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008)
        return

    try:
        current_user = get_user_from_token(token)

    except Exception:
        await websocket.close(code=1008)
        return

    
    await websocket.accept()

    session_id = str(uuid.uuid4())
    conversation_history = []
    background_tasks = set()
    latest_request_id = 0
    transcript_received_event = asyncio.Event()


    
    async def handle_final_transcript(transcript):

        nonlocal latest_request_id

        current_task = asyncio.current_task()
        background_tasks.add(current_task)

        # Assign a unique ID to every new question
        latest_request_id += 1
        request_id = latest_request_id

        transcript_received_event.set()

        try:
            await websocket.send_json({
                "type": "thinking",
                "message": "Processing your request..."
            })

            # Generate AI response
            result = await asyncio.to_thread(
                process_chat,
                question=transcript,
                session_id=session_id,
                history=conversation_history[-10:],
                employee_id=current_user.get("employee_id") or "",
                user_id=current_user["user_id"],
            )

            # Ignore old responses
            if request_id != latest_request_id:
                print("Ignoring outdated AI response.")
                return

            answer = result["answer"]

            # Generate speech only for the latest request
            audio_bytes = await asyncio.to_thread(
                text_to_speech,
                answer
            )

            # Check again because a newer question may have arrived
            if request_id != latest_request_id:
                print("Ignoring outdated audio response.")
                return

            conversation_history.append({
                "role": "user",
                "content": transcript
            })

            conversation_history.append({
                "role": "assistant",
                "content": answer
            })

            await websocket.send_json({
                "type": "ai_response",
                "transcript": transcript,
                "answer": answer,
                "sources": result.get("sources", []),
                "status": result.get("status"),
                "audio_available": bool(audio_bytes)
            })

            if audio_bytes:
                await websocket.send_bytes(audio_bytes)

        except WebSocketDisconnect:
            print("Browser disconnected during AI response.")

        except Exception as error:
            print("LIVE CHAT ERROR:", repr(error))

        finally:
            background_tasks.discard(current_task)



    try:
        await websocket.send_json({
            "type": "connection",
            "message": "Authenticated WebSocket connected!",
            "user_id": current_user["user_id"],
            "username": current_user["username"],
        })

        async with live_transcription_session(
            websocket,
            on_final_transcript=handle_final_transcript
        ) as dg_connection:

            await websocket.send_json({
                "type": "transcription_ready",
                "message": "Deepgram live transcription is ready!",
            })

            while True:
                message = await websocket.receive()

                if message["type"] == "websocket.disconnect":
                    break

                if message.get("bytes") is not None:

                    audio_chunk = message["bytes"]

                    await dg_connection.send_media(audio_chunk)

                elif message.get("text") is not None:

                    if message["text"] == "stop":

                        await dg_connection.send_finalize()

                        try:
                            await asyncio.wait_for(
                                transcript_received_event.wait(),
                                timeout=10
                            )

                        except asyncio.TimeoutError:
                            print("No final transcript received after stopping.")

                        # Wait for all pending AI responses.
                        while background_tasks:

                            pending_tasks = list(background_tasks)

                            await asyncio.gather(
                                *pending_tasks,
                                return_exceptions=True
                            )

                        await websocket.send_json({
                            "type": "stream_stopped",
                            "message": "Audio stream finalized."
                        })

                        break

    except WebSocketDisconnect:
        print(
            f"WebSocket disconnected: "
            f"{current_user['username']}"
        )
