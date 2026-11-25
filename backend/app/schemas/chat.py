
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=10000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=5000)
    session_id: str = "default"
    history: list[ChatMessage] = Field(default_factory=list)


class SourceReference(BaseModel):
    label: str
    filename: str
    page: int


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    status: str
    sources: list[SourceReference] = Field(default_factory=list)