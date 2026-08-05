from app.db import SessionLocal, engine
from app.models import Base, Role, User
from app.security import get_password_hash

Base.metadata.create_all(bind=engine)

db = SessionLocal()
try:
    if db.query(User).count() == 0:
        users = [
            ("admin", "admin@example.com", "Admin@123", Role.ADMIN),
            ("zsm", "zsm@example.com", "Zsm@123", Role.ZSM),
            ("tsm", "tsm@example.com", "Tsm@123", Role.TSM),
            ("asm", "asm@example.com", "Asm@123", Role.ASM),
            ("sr", "sr@example.com", "Sr@123", Role.SR),
        ]
        for username, email, password, role in users:
            db.add(User(username=username, email=email, hashed_password=get_password_hash(password), role=role))
        db.commit()
        print("Seeded demo users successfully")
    else:
        print("Users already exist")
finally:
    db.close()
