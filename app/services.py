from datetime import datetime
from sqlalchemy.orm import Session as DbSession
from fastapi import HTTPException, status

from app.models import Role, Session as SessionModel, Shop, User
from app.schemas import ShopCreate, UserCreate, LoginRequest
from app.security import get_password_hash, verify_password, create_session_key, get_session_expiration


def create_user(db: DbSession, payload: UserCreate) -> User:
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    user = User(
        name=payload.name,
        phone=payload.phone,
        cnic=payload.cnic,
        email=payload.email,
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
    user = db.query(User).filter(User.cnic == cnic).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


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
