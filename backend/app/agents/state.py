from typing import TypedDict


class AssistantState(TypedDict):
    question: str
    session_id: str
    history: list[dict]
    employee_id: str

    route: str
    rewritten_question: str
    context: str
    answer: str
    sources: list[dict]
    status: str

    # Leave confirmation workflow
    pending_leave: dict | None
    confirmation: str