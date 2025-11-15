from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt

from app.core.database import get_db
from app.core.config import settings
from app.crud.crud_user import user_crud
from app.models.sqlmodels import User
from app.models.schemas import TokenData
from app.core.constants import RoleID 

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Security(reusable_oauth2),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin đăng nhập.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        token_data = TokenData(sub=payload.get("sub"))
    except jwt.JWTError:
        raise credentials_exception
        
    if token_data.sub is None:
        raise credentials_exception
        
    user = user_crud.get_by_id(db, user_id=int(token_data.sub))
    
    if user is None:
        raise credentials_exception
        
    if user.IsDeleted or not user.IsActive:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Người dùng không hoạt động.")
        
    return user

def get_current_active_admin_or_moderator(current_user: User = Depends(get_current_user)) -> User:
    user_role_ids = {user_role.RoleID for user_role in current_user.user_roles}
    
    is_admin_or_moderator = RoleID.ADMIN in user_role_ids or RoleID.MODERATOR in user_role_ids
    
    if is_admin_or_moderator:
        return current_user
        
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Không có quyền truy cập. Yêu cầu quyền Admin hoặc Moderator."
    )

def get_current_active_customer(current_user: User = Depends(get_current_user)) -> User:
    user_role_ids = {user_role.RoleID for user_role in current_user.user_roles}
    
    if RoleID.CUSTOMER in user_role_ids:
        return current_user
        
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Không có quyền truy cập. Yêu cầu vai trò Customer."
    )