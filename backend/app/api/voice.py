
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response

from backend.app.services.speech_service import (
    speech_to_text,
    text_to_speech,
)
from backend.app.core.dependencies import get_current_user


router = APIRouter(
    prefix="/api/voice",
    tags=["Voice"],
)


@router.post("/transcribe")
def transcribe_audio(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Receive audio and convert it into text.
    Only authenticated users can use this endpoint.
    """

    allowed_types = {
        "audio/mpeg",
        "audio/mp3",
        "audio/wav",
        "audio/x-wav",
        "audio/webm",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio format.",
        )

    audio_bytes = file.file.read()

    if not audio_bytes:
        raise HTTPException(
            status_code=400,
            detail="Audio file is empty.",
        )

    if len(audio_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Audio file must be smaller than 10 MB.",
        )

    try:
        transcript = speech_to_text(audio_bytes)

        return {
            "transcript": transcript,
            "user_id": current_user["user_id"],
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Speech transcription failed.",
        )

@router.post("/speak")
def generate_speech(
    text: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        audio_bytes = text_to_speech(text)

        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=response.mp3"
            },
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Speech generation failed.",
        )
