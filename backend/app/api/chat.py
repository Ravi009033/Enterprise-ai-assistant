from fastapi import APIRouter, HTTPException

from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.services.chat_service import process_chat


router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    try:
        result = process_chat(
            question=request.question,
            session_id=request.session_id,
            history=[
                message.model_dump()
                for message in request.history
            ]
        )

        return result

    except Exception as error:

        print("CHAT API ERROR:", repr(error))

        raise HTTPException(
            status_code=500,
            detail="Unable to process chat request"
        ) from error