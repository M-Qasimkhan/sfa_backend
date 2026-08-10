from fastapi import FastAPI

from app.db import Base, engine
from app.models import Attendance, Session, Shop, User  # noqa: F401
from app.routers import router

app = FastAPI(title="Golden Foods SFA", version="1.0.0")

Base.metadata.create_all(bind=engine)

app.include_router(router)


@app.get("/")
def root():
    return {"message": "Golden Foods SFA API is running"}
