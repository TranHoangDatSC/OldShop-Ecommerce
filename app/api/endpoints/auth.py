from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core import security
from app.models import schemas
from app.crud.crud_user import user_crud

router = APIRouter(
    tags=["Authentication"]
)

@router.post("/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def register_user(
    user_in: schemas.UserCreate, 
    db: Session = Depends(get_db)
):
    # Kiểm tra Email đã tồn tại (sử dụng Email theo đúng casing của bạn)
    user = user_crud.get_by_email(db, email=user_in.Email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã được đăng ký. Vui lòng sử dụng email khác."
        )
    # Hàm create đã được custom trong crud_user.py để xử lý hash và role
    return user_crud.create(db, obj_in=user_in)


@router.post("/token", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """
    Xác thực và trả về JWT Access Token (sử dụng Form Data).
    """
    user = user_crud.authenticate(
        db, 
        email=form_data.username, 
        password=form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai email hoặc mật khẩu.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    elif not user.IsActive:
        # Đây là thông báo riêng biệt cho người dùng/Admin biết tài khoản bị khóa.
        # Vẫn dùng 401 vì đây là lỗi truy cập.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản của bạn đã bị vô hiệu hóa. Vui lòng liên hệ quản trị viên.", # <--- THÔNG BÁO RIÊNG
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = security.create_access_token(
        subject=user.UserID 
    )
    
    user_roles = [ur.role.RoleName for ur in user.user_roles if ur.role and not ur.role.IsDeleted]
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "roles": user_roles # Thêm danh sách vai trò
    }
    
    