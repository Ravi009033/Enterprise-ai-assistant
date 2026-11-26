
from fastapi import APIRouter, Depends, HTTPException

from backend.app.db.database import SessionLocal
from backend.app.models.leave_request import LeaveRequest
from backend.app.services.approval_service import (
    approve_leave_request,
    reject_leave_request,
)
from backend.app.core.dependencies import require_roles
from backend.app.db.database import SessionLocal
from backend.app.models.user import User


router = APIRouter(
    prefix="/api/hr",
    tags=["HR Management"],
)


@router.get("/leave-requests")
def get_pending_leave_requests(
    current_user: dict = Depends(require_roles("hr")),
):

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
def approve_request(
    request_id: int,
    current_user: dict = Depends(require_roles("hr")),
):

    try:
        return approve_leave_request(request_id)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.post("/leave-requests/{request_id}/reject")
def reject_request(
    request_id: int,
    current_user: dict = Depends(require_roles("hr")),
):

    try:
        return reject_leave_request(request_id)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )



@router.get("/profile")
def get_hr_profile(
    current_user: dict = Depends(require_roles("hr")),
):
    db = SessionLocal()

    try:
        user = db.query(User).filter(
            User.id == current_user["user_id"]
        ).first()

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="HR profile not found",
            )

        return {
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "account_status": "active" if user.is_active else "inactive",
        }

    finally:
        db.close()
