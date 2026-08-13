from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session as DbSession

from app.auth import clear_session_cookie, get_current_user, require_roles
from app.config import settings
from app.db import get_db
from app.models import Attendance, Role, User
from app.schemas import AttendanceCheckIn, AttendanceCheckout, AttendanceBreakEnd, AttendanceBreakStart, AttendanceOut, AuthResponse, AssignUserRequest, LeaveCreate, LeaveOut, LeaveStatusUpdate, LoginRequest, ShopCreate, ShopOut, UserCreate, UserOut, UserUpdate
from app.services import (
    authenticate_user,
    assign_user_to_parent,
    check_in,
    check_out,
    create_leave,
    create_session_for_user,
    create_shop,
    create_user,
    clear_user_sessions,
    end_break,
    get_attendance_for_user_by_month,
    get_leaves_for_user,
    get_leaves_under_manager,
    get_user_by_cnic,
    get_all_shops,
    get_all_users,
    get_direct_reports,
    get_users_by_area,
    get_users_under_me,
    start_break,
    update_current_user,
    update_leave_status,
)

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: DbSession = Depends(get_db)):
    user = create_user(db, payload)
    return user


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response, db: DbSession = Depends(get_db)):
    user = authenticate_user(db, payload)
    session_key, _ = create_session_for_user(db, user)
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=session_key,
        httponly=True,
        samesite="lax",
        max_age=settings.SESSION_EXPIRE_MINUTES * 60,
        secure=False,
    )
    print(f"User {user.email} logged in successfully. Session key: {session_key}")
    return {"message": "Login successful", "user": user, "session_key": session_key}


@router.post("/logout")
def logout(response: Response, user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    clear_user_sessions(db, user.id)
    clear_session_cookie(response)
    return {"message": "Logged out"}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.get("/users", response_model=list[UserOut])
def list_users(user: User = Depends(require_roles(Role.ADMIN)), db: DbSession = Depends(get_db)):
    return get_all_users(db)


@router.get("/users/by-cnic/{cnic}", response_model=UserOut)
def get_user_by_cnic_route(cnic: str, user: User = Depends(require_roles(Role.ADMIN)), db: DbSession = Depends(get_db)):
    return get_user_by_cnic(db, cnic)


@router.post("/users/assign", response_model=UserOut)
def assign_user_route(payload: AssignUserRequest, user: User = Depends(require_roles(Role.ADMIN)), db: DbSession = Depends(get_db)):
    return assign_user_to_parent(db, payload.child_id, payload.parent_id)


@router.get("/users/reports", response_model=list[UserOut])
def get_direct_reports_route(user: User = Depends(require_roles(Role.ZSM, Role.TSM, Role.ASM)), db: DbSession = Depends(get_db)):
    return get_direct_reports(db, user)


@router.get("/users/under-me", response_model=list[UserOut])
def get_users_under_me_route(
    user: User = Depends(require_roles(Role.ADMIN, Role.ZSM, Role.TSM, Role.ASM, Role.SR)),
    db: DbSession = Depends(get_db),
):
    return get_users_under_me(db, user)


@router.put("/me", response_model=UserOut)
def update_me(payload: UserUpdate, user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    return update_current_user(db, user, payload)


@router.get("/users/search", response_model=list[UserOut])
def search_users_by_area(area: str, user: User = Depends(require_roles(Role.ADMIN)), db: DbSession = Depends(get_db)):
    return get_users_by_area(db, area)


@router.post("/attendance/checkin", response_model=AttendanceOut)
def attendance_checkin_route(
    payload: AttendanceCheckIn,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    return check_in(db, user, payload)


@router.post("/attendance/break/start", response_model=AttendanceOut)
def attendance_break_start_route(
    payload: AttendanceBreakStart,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    return start_break(db, user, payload)


@router.post("/attendance/break/end", response_model=AttendanceOut)
def attendance_break_end_route(
    payload: AttendanceBreakEnd,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    return end_break(db, user, payload)


@router.post("/attendance/checkout", response_model=AttendanceOut)
def attendance_checkout_route(
    payload: AttendanceCheckout,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    return check_out(db, user, payload)


@router.post("/leaves", response_model=LeaveOut, status_code=status.HTTP_201_CREATED)
def create_leave_route(
    payload: LeaveCreate,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    return create_leave(db, user, payload)


@router.get("/leaves", response_model=list[LeaveOut])
def list_my_leaves_route(
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    return get_leaves_for_user(db, user)


@router.get("/leaves/under-me", response_model=list[LeaveOut])
def list_leaves_under_me_route(
    user: User = Depends(require_roles(Role.ADMIN, Role.ZSM, Role.TSM, Role.ASM)),
    db: DbSession = Depends(get_db),
):
    return get_leaves_under_manager(db, user)


@router.post("/leaves/{leave_id}/status", response_model=LeaveOut)
def set_leave_status_route(
    leave_id: int,
    payload: LeaveStatusUpdate,
    user: User = Depends(require_roles(Role.ADMIN, Role.ZSM, Role.TSM, Role.ASM)),
    db: DbSession = Depends(get_db),
):
    return update_leave_status(db, leave_id, payload.status)


@router.get("/attendance", response_model=list[AttendanceOut])
def get_my_attendance_route(
    month: int,
    year: int,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    return get_attendance_for_user_by_month(db, user.cnic, month, year)


@router.get("/attendance/user/{cnic}", response_model=list[AttendanceOut])
def get_user_attendance_route(
    cnic: str,
    month: int,
    year: int,
    user: User = Depends(require_roles(Role.ADMIN)),
    db: DbSession = Depends(get_db),
):
    return get_attendance_for_user_by_month(db, cnic, month, year)


@router.post("/create_shops", response_model=ShopOut, status_code=status.HTTP_201_CREATED)
def create_shop_route(
    payload: ShopCreate,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    return create_shop(db, payload, user.id)


@router.get("/shops", response_model=list[ShopOut])
def list_shops_route(user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    return get_all_shops(db)
