
from fastapi import APIRouter, HTTPException

from backend.app.db.database import SessionLocal
from backend.app.models.leave_request import LeaveRequest
from backend.app.services.approval_service import (
    approve_leave_request,
    reject_leave_request,
)

router = APIRouter(
    prefix="/api/hr",
    tags=["HR Management"],
)


@router.get("/leave-requests")
def get_pending_leave_requests():

    db = SessionLocal()

    try:
        requests = (
            db.query(LeaveRequest)
            .filter(LeaveRequest.status == "pending")
            .order_by(LeaveRequest.created_at.desc())
            .all()
        )

        return [
            {
                "request_id": request.id,
                "employee_id": request.employee_id,
                "days": request.days,
                "reason": request.reason,
                "status": request.status,
                "created_at": request.created_at,
            }
            for request in requests
        ]

    finally:
        db.close()


@router.post("/leave-requests/{request_id}/approve")
def approve_request(request_id: int):

    try:
        return approve_leave_request(request_id)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.post("/leave-requests/{request_id}/reject")
def reject_request(request_id: int):

    try:
        return reject_leave_request(request_id)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )
