
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.core.dependencies import get_user_from_token
from backend.app.services.speech_service import live_transcription_session
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
    chat_lock = asyncio.Lock()
    transcript_received_event = asyncio.Event()


    
    async def handle_final_transcript(transcript):

        current_task = asyncio.current_task()
        background_tasks.add(current_task)
        transcript_received_event.set()

        try:
            async with chat_lock:

                await websocket.send_json({
                    "type": "thinking",
                    "message": "Processing your request..."
                })

                result = await asyncio.to_thread(
                    process_chat,
                    question=transcript,
                    session_id=session_id,
                    history=conversation_history[-10:],
                    employee_id=current_user.get("employee_id") or "",
                    user_id=current_user["user_id"],
                )

                answer = result["answer"]

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
                    "status": result.get("status")
                })

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
