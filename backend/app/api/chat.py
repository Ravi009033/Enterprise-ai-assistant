
from fastapi import APIRouter, Depends, HTTPException

from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.services.chat_service import process_chat
from backend.app.core.dependencies import require_roles


router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user: dict = Depends(require_roles("employee", "hr")),
):

    employee_id = current_user.get("employee_id")

    

    try:
        result = process_chat(
            question=request.question,
            session_id=request.session_id,
            history=[
                message.model_dump()
                for message in request.history
            ],
            employee_id=employee_id,
            user_id=current_user["user_id"],
        )

        return result

    except Exception as error:
        print("CHAT API ERROR:", repr(error))

        raise HTTPException(
            status_code=500,
            detail="Unable to process chat request",
        ) from error
