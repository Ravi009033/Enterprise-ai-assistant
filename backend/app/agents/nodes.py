
from backend.app.core.llm import get_llm
from backend.app.rag.query_rewriter import rewrite_query
from backend.app.rag.retrieval import retrieve_relevant_documents
from backend.app.services.employee_service import get_leave_balance
from backend.app.services.leave_service import apply_for_leave
from typing import Literal
from pydantic import BaseModel, Field


def router_node(state: dict) -> dict:
    
    """
    Classifies the user's question into:
    rag, general, or tool.
    """

    question = state["question"]

    # If a leave request is awaiting confirmation,
        # send the next message directly to the tool node.
    if state.get("pending_leave"):
        print("Pending leave confirmation detected.")
        return {"route": "tool"}
    
    prompt = f"""
You are an intelligent enterprise assistant router.

Classify the user's question into exactly one category:

1. rag:
   Questions about company documents, uploaded PDFs,
   policies, procedures, rules, or internal knowledge.

2. general:
   General knowledge, programming, explanations,
   greetings, or normal conversation.

3. tool:
   Requests requiring an external enterprise system,
   such as employee leave balance, attendance records,
   payroll, database queries, or HR information.

Rules:
- Return only one word.
- Allowed outputs: rag, general, tool.
- Do not explain your decision.

User question:
{question}

Category:
"""

    llm = get_llm()

    response = llm.invoke(prompt)

    content = response.content

    if isinstance(content, list):
        content = "\n".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict)
            and item.get("type") == "text"
        )

    route = content.strip().lower()

    if route not in {"rag", "general", "tool"}:
        route = "general"

    print(f"User question: {question}")
    print(f"Selected route: {route}")

    return {
        "route": route
    }


def rag_node(state: dict) -> dict:
    question = state["question"]
    history = state.get("history", [])

    standalone_question = rewrite_query(
        question=question,
        history=history
    )

    print("RAG rewritten question:", standalone_question)

    documents = retrieve_relevant_documents(
        question=standalone_question,
        k=4,
        score_threshold=0.50
    )

    if not documents:
        return {
            "rewritten_question": standalone_question,
            "context": "",
            "answer": (
                "I couldn't find relevant information in "
                "the uploaded documents to answer your question."
            ),
            "sources": [],
            "status": "no_relevant_documents"
        }

    context_parts = []
    sources = []
    source_labels = {}

    for document in documents:
        filename = document.metadata.get(
            "source", "Unknown document"
        )
        page = document.metadata.get("page", "Unknown")

        source_key = (filename, page)

        if source_key not in source_labels:
            label = f"Source {len(source_labels) + 1}"
            source_labels[source_key] = label

            sources.append({
                "label": label,
                "filename": filename,
                "page": page
            })

        label = source_labels[source_key]

        context_parts.append(
            f"[{label}: {filename}, Page {page}]\n"
            f"{document.page_content}"
        )

    context = "\n\n".join(context_parts)

    prompt = f"""
You are an enterprise document assistant.

Answer the user's question using only the provided context.

Rules:
1. Do not invent facts.
2. Cite supporting information using [Source 1] format.
3. Use only source labels provided in the context.
4. If information is missing, say so clearly.

Context:
{context}

User question:
{question}

Answer:
"""

    response = get_llm().invoke(prompt)
    content = response.content

    if isinstance(content, list):
        content = "\n".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict)
            and item.get("type") == "text"
        )

    return {
        "rewritten_question": standalone_question,
        "context": context,
        "answer": content,
        "sources": sources,
        "status": "success"
    }


def general_node(state: dict) -> dict:
    question = state["question"]

    prompt = f"""
You are a helpful AI assistant.

Answer the user's question clearly and accurately.

Question:
{question}
"""

    response = get_llm().invoke(prompt)
    content = response.content

    if isinstance(content, list):
        content = "\n".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict)
            and item.get("type") == "text"
        )

    return {
        "answer": content,
        "sources": [],
        "status": "success"
    }



def tool_node(state: dict) -> dict:
    employee_id = state.get("employee_id")

    if not employee_id:
        return {
            "answer": "Employee identity is not configured.",
            "sources": [],
            "status": "identity_not_configured",
        }
    
    pending_leave = state.get("pending_leave")

    if pending_leave:
        confirmation = state.get("confirmation", "unknown")

        # User confirms the leave request.
        if confirmation == "yes":
            try:
                result = apply_for_leave(
                    employee_id=employee_id,
                    days=pending_leave["days"],
                    reason=pending_leave["reason"],
                    idempotency_key=state["session_id"],
                )

                return {
                    "answer": (
                        "Leave request submitted successfully.\n"
                        f"Request ID: {result['request_id']}\n"
                        f"Days requested: {result['days']}\n"
                        f"Status: {result['status']}"
                    ),
                    "pending_leave": {},
                    "sources": [],
                    "status": "success",
                }

            except ValueError as error:
                return {
                    "answer": str(error),
                    "pending_leave": {},
                    "sources": [],
                    "status": "tool_error",
                }

            except Exception as error:
                print("LEAVE SUBMISSION ERROR:", repr(error))

                return {
                    "answer": "Unable to submit your leave request.",
                    "pending_leave": pending_leave,
                    "sources": [],
                    "status": "tool_error",
                }

        # User rejects the leave request.
        elif confirmation == "no":
            return {
                "answer": "Your leave request has been cancelled.",
                "pending_leave": {},
                "sources": [],
                "status": "cancelled",
            }

        # User has not given a clear confirmation.
        else:
            return {
                "answer": (
                    "Your leave request is still pending confirmation.\n"
                    "Please reply YES to submit or NO to cancel."
                ),
                "pending_leave": pending_leave,
                "sources": [],
                "status": "awaiting_confirmation",
            }
        
    try:
        details = extract_leave_details(state["question"])

        action = details["action"]

        if action == "check_balance":
            leave_data = get_leave_balance(employee_id)

            answer = (
                f"Hello {leave_data['employee_name']}! "
                f"Your remaining leave balance is "
                f"{leave_data['remaining_leaves']} days."
            )

            return {
                "answer": answer,
                "sources": [],
                "status": "success",
            }

        
        if action == "apply_leave":
            days = details.get("days")
            reason = details.get("reason")

            if days is None or reason is None:
                return {
                    "answer": (
                        "Please provide both the number of leave days "
                        "and the reason for your leave."
                    ),
                    "sources": [],
                    "status": "missing_leave_details",
                }

            # Do not submit until the user confirms.
            return {
                "answer": (
                    f"You are requesting {days} days of leave "
                    f"for: {reason}.\n"
                    "Would you like me to submit this request? "
                    "Please reply YES or NO."
                ),
                "pending_leave": {
                    "days": days,
                    "reason": reason,
                },
                "sources": [],
                "status": "awaiting_confirmation",
            }

    except ValueError as error:
        return {
            "answer": str(error),
            "sources": [],
            "status": "tool_error",
        }

    except Exception as error:
        print("EMPLOYEE TOOL ERROR:", repr(error))

        return {
            "answer": "Unable to process your employee request.",
            "sources": [],
            "status": "tool_error",
        }



class LeaveDetails(BaseModel):
    action: Literal["apply_leave", "check_balance"] = Field(
        description="The employee operation requested"
    )

    days: int | None = Field(
        default=None,
        ge=1,
        description="Number of leave days requested, or null"
    )

    reason: str | None = Field(
        default=None,
        description="Reason for leave, or null"
    )




def extract_leave_details(question: str) -> dict:

    prompt = f"""
Identify the employee's requested operation.

Rules:
1. Use apply_leave when the employee wants to submit a leave request.
2. Use check_balance when the employee asks about leave balance.
3. Extract the number of leave days if provided.
4. Extract the reason if provided.
5. Do not invent missing information.
6. Return the structured fields according to the schema.

Employee request:
{question}
"""

    try:
        structured_llm = get_llm().with_structured_output(
            LeaveDetails,
            method="json_schema",
        )

        details = structured_llm.invoke(prompt)

        return details.model_dump()

    except Exception as error:
        print("LEAVE EXTRACTION ERROR:", repr(error))
        raise ValueError(
            "Unable to understand the leave request. Please try again."
        ) from error
