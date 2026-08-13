from datetime import date, datetime
from sqlalchemy.orm import Session as DbSession
from fastapi import HTTPException, status

from app.models import Attendance, LeaveRequest, Role, Session as SessionModel, Shop, User
from app.schemas import AttendanceBreakEnd, AttendanceBreakStart, AttendanceCheckout, AttendanceCheckIn, LeaveCreate, ShopCreate, UserCreate, LoginRequest, UserUpdate
from app.security import get_password_hash, verify_password, create_session_key, get_session_expiration


def get_users_under_me(db: DbSession, manager: User) -> list[User]:
    if manager.role == Role.ADMIN:
        return (
            db.query(User)
            .filter(User.role.in_([Role.ZSM, Role.TSM, Role.ASM, Role.SR]))
            .order_by(User.created_at.desc())
            .all()
        )

    if manager.role == Role.ZSM:
        children = db.query(User).filter(User.zsm_id == manager.id, User.role == Role.TSM).all()
    elif manager.role == Role.TSM:
        children = db.query(User).filter(User.tsm_id == manager.id, User.role == Role.ASM).all()
    elif manager.role == Role.ASM:
        children = db.query(User).filter(User.asm_id == manager.id, User.role == Role.SR).all()
    else:
        return []

    descendants: list[User] = []
    for child in children:
        descendants.append(child)
        descendants.extend(get_users_under_me(db, child))

    return descendants


def create_user(db: DbSession, payload: UserCreate) -> User:
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    user = User(
        name=payload.name,
        phone=payload.phone,
        cnic=payload.cnic,
        email=payload.email,
        area=payload.area,
        password=get_password_hash(payload.password),
        image=payload.image,
        role=payload.role if isinstance(payload.role, Role) else Role[payload.role],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: DbSession, payload: LoginRequest) -> User:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return user


def update_current_user(db: DbSession, user: User, payload: "UserUpdate") -> User:
    if payload.email and payload.email != user.email:
        if db.query(User).filter(User.email == payload.email).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
        user.email = payload.email

    if payload.name is not None:
        user.name = payload.name
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.cnic is not None:
        user.cnic = payload.cnic
    if payload.area is not None:
        user.area = payload.area
    if payload.image is not None:
        user.image = payload.image

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_session_for_user(db: DbSession, user: User) -> tuple[str, datetime]:
    session_key = create_session_key()
    expires_at = get_session_expiration()
    session = SessionModel(session_key=session_key, user_id=user.id, expires_at=expires_at)
    db.add(session)
    db.commit()
    return session_key, expires_at


def clear_user_sessions(db: DbSession, user_id: int) -> None:
    db.query(SessionModel).filter(SessionModel.user_id == user_id).delete()
    db.commit()


def get_user_by_id(db: DbSession, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def get_user_by_cnic(db: DbSession, cnic: str) -> User:
    # ensure CNIC is compared as string to match the DB column type
    cnic = str(cnic)
    user = db.query(User).filter(User.cnic == cnic).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def assign_user_to_parent(db: DbSession, child_id: int, parent_id: int) -> User:
    child = db.query(User).filter(User.id == child_id).first()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child user not found")

    parent = db.query(User).filter(User.id == parent_id).first()
    if not parent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent user not found")

    if child.role == Role.TSM and parent.role == Role.ZSM:
        child.zsm_id = parent.id
    elif child.role == Role.ASM and parent.role == Role.TSM:
        child.tsm_id = parent.id
    elif child.role == Role.SR and parent.role == Role.ASM:
        child.asm_id = parent.id
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role relationship: child and parent roles must follow ZSM -> TSM -> ASM -> SR",
        )

    db.add(child)
    db.commit()
    db.refresh(child)
    return child


def get_direct_reports(db: DbSession, manager: User) -> list[User]:
    if manager.role == Role.ZSM:
        return (
            db.query(User)
            .filter(User.zsm_id == manager.id, User.role == Role.TSM)
            .order_by(User.created_at.desc())
            .all()
        )
    if manager.role == Role.TSM:
        return (
            db.query(User)
            .filter(User.tsm_id == manager.id, User.role == Role.ASM)
            .order_by(User.created_at.desc())
            .all()
        )
    if manager.role == Role.ASM:
        return (
            db.query(User)
            .filter(User.asm_id == manager.id, User.role == Role.SR)
            .order_by(User.created_at.desc())
            .all()
        )
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only ZSM, TSM, and ASM users can view direct reports")


def create_shop(db: DbSession, payload: ShopCreate, created_by_id: int | None) -> Shop:
    existing = db.query(Shop).filter(Shop.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shop with this name already exists")

    shop = Shop(
        name=payload.name.strip(),
        address=payload.address,
        phone=payload.phone,
        image=payload.image,
        latitude=payload.latitude,
        longitude=payload.longitude,
        created_by_id=created_by_id,
    )
    db.add(shop)
    db.commit()
    db.refresh(shop)
    return shop


def get_all_shops(db: DbSession) -> list[Shop]:
    return db.query(Shop).order_by(Shop.created_at.desc()).all()


def get_all_users(db: DbSession) -> list[User]:
    return db.query(User).order_by(User.created_at.desc()).all()


def get_users_by_area(db: DbSession, area: str) -> list[User]:
    query_area = area.strip()
    return (
        db.query(User)
        .filter(User.area.ilike(f"%{query_area}%"))
        .order_by(User.created_at.desc())
        .all()
    )


def get_or_create_attendance(db: DbSession, user: User, date_value: date) -> Attendance:
    attendance = (
        db.query(Attendance)
        .filter(Attendance.user_id == user.id, Attendance.date == date_value)
        .first()
    )
    if attendance is None:
        attendance = Attendance(
            user_id=user.id,
            date=date_value,
            day=date_value.day,
            month=date_value.month,
            year=date_value.year,
        )
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
    return attendance


def check_in(db: DbSession, user: User, payload: "AttendanceCheckIn") -> Attendance:
    attendance = get_or_create_attendance(db, user, payload.date)
    attendance.check_in = payload.check_in
    attendance.check_in_location = payload.check_in_location
    attendance.day = payload.date.day
    attendance.month = payload.date.month
    attendance.year = payload.date.year

    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance


def start_break(db: DbSession, user: User, payload: "AttendanceBreakStart") -> Attendance:
    attendance = get_or_create_attendance(db, user, date.today())
    attendance.break_start = payload.break_start
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance


def end_break(db: DbSession, user: User, payload: "AttendanceBreakEnd") -> Attendance:
    attendance = get_or_create_attendance(db, user, date.today())
    attendance.break_end = payload.break_end
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance


def check_out(db: DbSession, user: User, payload: "AttendanceCheckout") -> Attendance:
    attendance = get_or_create_attendance(db, user, date.today())
    attendance.check_out = payload.check_out
    attendance.check_out_location = payload.check_out_location
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance


def create_leave(db: DbSession, user: User, payload: "LeaveCreate") -> LeaveRequest:
    leave_request = LeaveRequest(
        user_id=user.id,
        category=payload.category.strip(),
        start_date=payload.start_date,
        end_date=payload.end_date,
        reason=payload.reason.strip(),
        evidence_image=payload.evidence_image,
    )
    db.add(leave_request)
    db.commit()
    db.refresh(leave_request)
    return leave_request


def update_leave_status(db: DbSession, leave_id: int, status_value: bool) -> LeaveRequest:
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")
    leave_request.status = status_value
    db.add(leave_request)
    db.commit()
    db.refresh(leave_request)
    return leave_request


def get_leaves_for_user(db: DbSession, user: User) -> list[LeaveRequest]:
    return (
        db.query(LeaveRequest)
        .filter(LeaveRequest.user_id == user.id)
        .order_by(LeaveRequest.start_date.desc())
        .all()
    )


def get_leaves_for_users(db: DbSession, user_ids: list[int]) -> list[LeaveRequest]:
    if not user_ids:
        return []
    return (
        db.query(LeaveRequest)
        .filter(LeaveRequest.user_id.in_(user_ids))
        .order_by(LeaveRequest.start_date.desc())
        .all()
    )


def get_leaves_under_manager(db: DbSession, manager: User) -> list[LeaveRequest]:
    report_users = get_users_under_me(db, manager)
    report_ids = [report.id for report in report_users]
    return get_leaves_for_users(db, report_ids)


def get_attendance_for_user_by_month(db: DbSession, cnic: str, month: int, year: int) -> list[Attendance]:
    user = get_user_by_cnic(db, cnic)
    return (
        db.query(Attendance)
        .filter(Attendance.user_id == user.id, Attendance.month == month, Attendance.year == year)
        .order_by(Attendance.date)
        .all()
    )
