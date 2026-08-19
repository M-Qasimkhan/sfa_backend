from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session as DbSession

from app.auth import clear_session_cookie, get_current_user, require_roles
from app.config import settings
from app.db import get_db
from app.models import Attendance, Category, Product, Role, User
from app.schemas import (
    AttendanceCheckIn,
    AttendanceCheckout,
    AttendanceBreakEnd,
    AttendanceBreakStart,
    AttendanceOut,
    AuthResponse,
    AssignUserRequest,
    CategoryCreate,
    CategoryOut,
    CategoryUpdate,
    LeaveCreate,
    LeaveOut,
    LeaveStatusUpdate,
    LoginRequest,
    ProductCreate,
    ProductOut,
    ProductUpdate,
    ShopCreate,
    ShopOut,
    UserCreate,
    UserOut,
    UserUpdate,
)
from app.services import (
    authenticate_user,
    assign_user_to_parent,
    check_in,
    check_out,
    create_category,
    create_leave,
    create_product,
    create_session_for_user,
    create_shop,
    create_user,
    clear_user_sessions,
    delete_category,
    delete_product,
    end_break,
    get_all_categories,
    get_all_products,
    get_all_shops,
    get_all_users,
    get_attendance_for_user_by_month,
    get_leaves_for_user,
    get_products_by_category,
    get_leaves_under_manager,
    get_user_by_cnic,
    search_products,
    get_direct_reports,
    get_users_by_area,
    get_users_under_me,
    start_break,
    update_category,
    update_current_user,
    update_leave_status,
    update_product,
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


@router.post("/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category_route(payload: CategoryCreate, user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    return create_category(db, payload)


@router.get("/categories", response_model=list[CategoryOut])
def list_categories_route(user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    return get_all_categories(db)


@router.get("/categories/{category_id}", response_model=CategoryOut)
def get_category_route(category_id: int, user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    return db.query(Category).filter(Category.id == category_id).first()


@router.put("/categories/{category_id}", response_model=CategoryOut)
def update_category_route(
    category_id: int,
    payload: CategoryUpdate,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    return update_category(db, category_id, payload)


@router.delete("/categories/{category_id}")
def delete_category_route(category_id: int, user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    delete_category(db, category_id)
    return {"message": "Category deleted successfully"}


@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product_route(payload: ProductCreate, user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    return create_product(db, payload)


@router.get("/products", response_model=list[ProductOut])
def list_products_route(
    category_id: int | None = None,
    search: str | None = None,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    return get_all_products(db, category_id=category_id, search=search)


@router.get("/products/search", response_model=list[ProductOut])
def search_products_route(
    q: str,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    return search_products(db, q)


@router.get("/categories/{category_id}/products", response_model=list[ProductOut])
def list_products_by_category_route(
    category_id: int,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    return get_products_by_category(db, category_id)


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product_route(product_id: int, user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    return db.query(Product).filter(Product.id == product_id).first()


@router.post("/products/{product_id}/upload-image")
def upload_product_image_route(
    product_id: int,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    upload_dir = "uploads/products"
    import os

    os.makedirs(upload_dir, exist_ok=True)
    file_name = f"{product_id}_{file.filename}"
    file_path = os.path.join(upload_dir, file_name)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    product.image = f"/{file_path.replace('\\', '/')}"
    db.add(product)
    db.commit()
    db.refresh(product)
    return {"message": "Image uploaded successfully", "image": product.image}


@router.put("/products/{product_id}", response_model=ProductOut)
def update_product_route(
    product_id: int,
    payload: ProductUpdate,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    return update_product(db, product_id, payload)


@router.delete("/products/{product_id}")
def delete_product_route(product_id: int, user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    delete_product(db, product_id)
    return {"message": "Product deleted successfully"}
