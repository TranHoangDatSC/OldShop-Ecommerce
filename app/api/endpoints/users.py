# app/api/endpoints/users.py (Đã sửa đổi - Bỏ kiểm tra Token)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List

from app.core.database import get_db
from app.models import schemas, sqlmodels
from app.crud.crud_user import user_crud
# KHÔNG CẦN NHẬP get_current_user NỮA
# from app.api.deps import get_current_user 
from app.models.schemas import UserCreate
from app.core.constants import RoleID

router = APIRouter()

# --- 1. ROUTE TẠO MODERATOR (Không cần đăng nhập) ---
@router.post("/moderator", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_moderator_account(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    # ĐÃ XÓA: current_user: sqlmodels.User = Depends(get_current_user) 
) -> Any:
    """
    Tạo tài khoản Moderator mới. (Không yêu cầu đăng nhập)
    """
    
    # 1. Kiểm tra username và email đã tồn tại chưa
    if user_crud.get_by_email(db, user_in.Email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã được đăng ký."
        )
    if user_crud.get_by_username(db, user_in.Username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username đã được sử dụng."
        )

    try:
        # 2. Gọi hàm tạo Moderator (tự động gán role_id=2)
        moderator = user_crud.create_moderator(db, obj_in=user_in)
        return moderator
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"Lỗi DB/Server khi tạo Moderator: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Lỗi server khi tạo Moderator.")

# --- 2. ROUTE LẤY DANH SÁCH MODERATOR (Không cần đăng nhập) ---
@router.get("/moderator", response_model=List[schemas.User])
def read_moderators(
    db: Session = Depends(get_db),
    skip: int = 0, 
    limit: int = 100,
    # ĐÃ XÓA: current_user: sqlmodels.User = Depends(get_current_user)
) -> Any:
    """Lấy danh sách tất cả các tài khoản Moderator đang hoạt động."""
    
    all_users = user_crud.get_multiple(db, skip=skip, limit=limit)
    
    moderators = [
        user for user in all_users 
        if any(user_role.RoleID == RoleID.MODERATOR for user_role in user.user_roles)
    ]
    
    return moderators

# --- 3. ROUTE LẤY CHI TIẾT MODERATOR THEO ID (Không cần đăng nhập) ---
@router.get("/moderator/{user_id}", response_model=schemas.User)
def read_moderator_by_id(
    user_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """Lấy thông tin chi tiết của một Moderator theo UserID."""
    user = user_crud.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy Moderator.")
    
    # Kiểm tra đảm bảo đây là Moderator (RoleID=2) hoặc Admin (RoleID=1) 
    # (Tạm thời bỏ qua kiểm tra Admin vì Admin Dashboard có thể chỉnh sửa cả Admin)
    is_moderator = any(user_role.RoleID == RoleID.MODERATOR for user_role in user.user_roles)
    
    if not is_moderator:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ID này không phải của Moderator.")

    return user

# --- 4. ROUTE CẬP NHẬT THÔNG TIN MODERATOR (Không cần đăng nhập) ---
@router.put("/moderator/{user_id}", response_model=schemas.User)
def update_moderator(
    user_id: int,
    user_in: schemas.UserUpdate, # Sử dụng schema UserUpdate mới
    db: Session = Depends(get_db),
) -> Any:
    """Cập nhật thông tin của một Moderator (bao gồm cả mật khẩu nếu cung cấp)."""
    user = user_crud.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy Moderator.")
    
    # Kiểm tra đảm bảo đây là Moderator
    is_moderator = any(user_role.RoleID == RoleID.MODERATOR for user_role in user.user_roles)
    if not is_moderator:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ID này không phải của Moderator.")

    # Kiểm tra xem Email hoặc Username mới có bị trùng với người khác không
    if user_in.Email and user_in.Email != user.Email and user_crud.get_by_email(db, user_in.Email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email đã được đăng ký bởi người khác.")
    
    if user_in.Username and user_in.Username != user.Username and user_crud.get_by_username(db, user_in.Username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username đã được sử dụng bởi người khác.")

    try:
        updated_user = user_crud.update(db, db_obj=user, obj_in=user_in)
        return updated_user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"Lỗi DB/Server khi cập nhật Moderator: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Lỗi server khi cập nhật Moderator.")

# --- 5. ROUTE LẤY DANH SÁCH KHÁCH HÀNG (RoleID=3) ---
@router.get("/customer", response_model=List[schemas.User])
def read_customers(
    db: Session = Depends(get_db),
    skip: int = 0, 
    limit: int = 100,
) -> Any:
    """Lấy danh sách tất cả các tài khoản Khách hàng (RoleID=3)."""
    
    all_users = user_crud.get_multiple(db, skip=skip, limit=limit)
    
    # Lọc ra các tài khoản có RoleID là 3 (Khách hàng)
    customers = [
        user for user in all_users 
        if any(user_role.RoleID == RoleID.CUSTOMER for user_role in user.user_roles)
    ]
    
    return customers

# --- 6. ROUTE LẤY CHI TIẾT KHÁCH HÀNG THEO ID ---
@router.get("/customer/{user_id}", response_model=schemas.User)
def read_customer_by_id(
    user_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """Lấy thông tin chi tiết của một Khách hàng theo UserID."""
    user = user_crud.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy Khách hàng.")
    
    # Kiểm tra đảm bảo đây là Khách hàng (RoleID=3)
    is_customer = any(user_role.RoleID == RoleID.CUSTOMER for user_role in user.user_roles)
    
    if not is_customer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ID này không phải của Khách hàng.")

    return user

# --- 7. ROUTE CẬP NHẬT THÔNG TIN KHÁCH HÀNG (Bao gồm Khóa/Mở Khóa) ---
@router.put("/customer/{user_id}", response_model=schemas.User)
def update_customer(
    user_id: int,
    user_in: schemas.UserUpdate, # Sử dụng schema UserUpdate
    db: Session = Depends(get_db),
) -> Any:
    """Cập nhật thông tin của một Khách hàng (Username, Email, FullName, Password, IsActive)."""
    user = user_crud.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy Khách hàng.")
    
    # Kiểm tra đảm bảo đây là Khách hàng
    is_customer = any(user_role.RoleID == RoleID.CUSTOMER for user_role in user.user_roles)
    if not is_customer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ID này không phải của Khách hàng.")

    # 1. Kiểm tra Email hoặc Username mới có bị trùng với người khác không
    if user_in.Email and user_in.Email != user.Email and user_crud.get_by_email(db, user_in.Email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email đã được đăng ký bởi người khác.")
    
    if user_in.Username and user_in.Username != user.Username and user_crud.get_by_username(db, user_in.Username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username đã được sử dụng bởi người khác.")

    try:
        # 2. Cập nhật thông tin (CRUD update có thể xử lý cả IsActive, Password, và các trường khác)
        updated_user = user_crud.update(db, db_obj=user, obj_in=user_in)
        return updated_user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"Lỗi DB/Server khi cập nhật Khách hàng: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Lỗi server khi cập nhật Khách hàng.")