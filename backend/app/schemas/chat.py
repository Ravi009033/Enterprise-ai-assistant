
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):

    question: str = Field(
        min_length=1,
        max_length=5000
    )

    session_id: str = "default"

class ChatResponse(BaseModel):

    answer: str

    session_id: str

    status: str
