
from fastapi import APIRouter, Depends, HTTPException

from backend.app.core.dependencies import require_roles
from backend.app.db.database import SessionLocal
from backend.app.models.leave_request import LeaveRequest
from backend.app.services.employee_service import get_leave_balance
from backend.app.models.employee import Employee


router = APIRouter(
    prefix="/api/employee",
    tags=["Employee"],
)


@router.get("/leave-balance")
def employee_leave_balance(
    current_user: dict = Depends(require_roles("employee")),
):
    employee_id = current_user["employee_id"]

    if not employee_id:
        raise HTTPException(
            status_code=400,
            detail="Employee account is not linked to an employee record",
        )

    try:
        return get_leave_balance(employee_id)

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


@router.get("/leave-requests")
def get_employee_leave_requests(
    current_user: dict = Depends(require_roles("employee")),
):
    employee_id = current_user["employee_id"]

    if not employee_id:
        raise HTTPException(
            status_code=400,
            detail="Employee account is not linked to an employee record",
        )

    db = SessionLocal()

    try:
        requests = (
            db.query(LeaveRequest)
            .filter(
                LeaveRequest.employee_id == employee_id
            )
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



@router.get("/leave-requests/{request_id}")
def get_employee_leave_request(
    request_id: int,
    current_user: dict = Depends(require_roles("employee")),
):
    employee_id = current_user["employee_id"]

    if not employee_id:
        raise HTTPException(
            status_code=400,
            detail="Employee account is not linked to an employee record",
        )

    db = SessionLocal()

    try:
        request = (
            db.query(LeaveRequest)
            .filter(
                LeaveRequest.id == request_id,
                LeaveRequest.employee_id == employee_id,
            )
            .first()
        )

        if request is None:
            raise HTTPException(
                status_code=404,
                detail="Leave request not found",
            )

        return {
            "request_id": request.id,
            "employee_id": request.employee_id,
            "days": request.days,
            "reason": request.reason,
            "status": request.status,
            "created_at": request.created_at,
        }

    finally:
        db.close()



@router.get("/profile")
def get_employee_profile(
    current_user: dict = Depends(require_roles("employee")),
):
    employee_id = current_user["employee_id"]

    if not employee_id:
        raise HTTPException(
            status_code=400,
            detail="Employee account is not linked to an employee record",
        )

    db = SessionLocal()

    try:
        employee = db.query(Employee).filter(
            Employee.employee_id == employee_id
        ).first()

        if employee is None:
            raise HTTPException(
                status_code=404,
                detail="Employee profile not found",
            )

        return {
            "employee_id": employee.employee_id,
            "name": employee.name,
            "total_leaves": employee.total_leaves,
            "used_leaves": employee.used_leaves,
            "remaining_leaves": employee.remaining_leaves,
        }

    finally:
        db.close()
