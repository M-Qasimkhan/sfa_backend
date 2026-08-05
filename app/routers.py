from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session as DbSession

from app.auth import clear_session_cookie, get_current_user, require_roles
from app.db import get_db
from app.models import Role, User
from app.schemas import AuthResponse, LoginRequest, ShopCreate, ShopOut, UserCreate, UserOut
from app.services import (
    authenticate_user,
    create_session_for_user,
    create_shop,
    create_user,
    clear_user_sessions,
    get_user_by_id,
    get_user_by_cnic,
    get_all_shops,
    get_all_users,
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
        key="session_id",
        value=session_key,
        httponly=True,
        samesite="lax",
        max_age=3600,
        secure=False,
    )
    return {"message": "Login successful", "user": user}


@router.post("/logout")
def logout(response: Response, user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    clear_user_sessions(db, user.id)
    clear_session_cookie(response)
    return {"message": "Logged out"}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.get("/admin")
def admin(user: User = Depends(require_roles(Role.ADMIN))):
    return {"message": "Admin access granted", "user": user.name}


@router.get("/zsm")
def zsm(user: User = Depends(require_roles(Role.ZSM))):
    return {"message": "ZSM access granted", "user": user.name}


@router.get("/tsm")
def tsm(user: User = Depends(require_roles(Role.TSM))):
    return {"message": "TSM access granted", "user": user.name}


@router.get("/asm")
def asm(user: User = Depends(require_roles(Role.ASM))):
    return {"message": "ASM access granted", "user": user.name}


@router.get("/sr")
def sr(user: User = Depends(require_roles(Role.SR))):
    return {"message": "SR access granted", "user": user.name}


@router.get("/users", response_model=list[UserOut])
def list_users(user: User = Depends(require_roles(Role.ADMIN)), db: DbSession = Depends(get_db)):
    return get_all_users(db)


@router.get("/users/by-cnic/{cnic}", response_model=UserOut)
def get_user_by_cnic_route(cnic: str, user: User = Depends(require_roles(Role.ADMIN)), db: DbSession = Depends(get_db)):
    return get_user_by_cnic(db, cnic)


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, user: User = Depends(require_roles(Role.ADMIN)), db: DbSession = Depends(get_db)):
    return get_user_by_id(db, user_id)


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
