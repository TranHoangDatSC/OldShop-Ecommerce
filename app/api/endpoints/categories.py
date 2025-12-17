from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any
from app.api import deps
from app.models import schemas
from app.models.sqlmodels import User
from app.crud.crud_category import category_crud
from app.core.constants import RoleID

router = APIRouter()

# --- PUBLIC: Lấy danh sách category (SỬA DỤNG CRUD LAYER) ---
@router.get("/", response_model=List[schemas.Category])
def get_categories(db: Session = Depends(deps.get_db)) -> Any:
    """Lấy danh sách tất cả các Category chưa bị xóa."""
    # SỬA: Sử dụng category_crud.get_all để lấy tất cả category chưa bị xóa.
    return category_crud.get_all(db)

# Hàm read_categories không có decorator nên bị bỏ qua hoặc là lỗi định nghĩa. 
# Ta chỉ cần hàm có decorator @router.get("/")
# def read_categories(
#     skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)
# ):
#     categories = category_crud.get_multiple(db, skip=skip, limit=limit)
#     return categories

# --- PUBLIC: Lấy chi tiết category ---
@router.get("/{category_id}", response_model=schemas.Category)
def read_category(
    category_id: int, 
    db: Session = Depends(deps.get_db)
):
    category = category_crud.get_by_id(db, category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Danh mục không tồn tại."
        )
    return category

# --- PROTECTED: Tạo category ---
@router.post("/", response_model=schemas.Category, status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: schemas.CategoryCreate, 
    db: Session = Depends(deps.get_db), 
    current_user: User = Depends(deps.get_current_user)
):
    # Chỉ ADMIN hoặc MODERATOR mới được tạo
    user_role_ids = {user_role.RoleID for user_role in current_user.user_roles}
    if not (RoleID.ADMIN in user_role_ids or RoleID.MODERATOR in user_role_ids):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền tạo danh mục mới."
        )
    
    try:
        new_category = category_crud.create(db, obj_in=category_in)
        return new_category
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# --- PROTECTED: Cập nhật category ---
@router.put("/{category_id}", response_model=schemas.Category)
def update_category(
    category_id: int, 
    category_in: schemas.CategoryUpdate, 
    db: Session = Depends(deps.get_db), 
    current_user: User = Depends(deps.get_current_user)
):
    category = category_crud.get_by_id(db, category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Danh mục không tồn tại."
        )
        
    user_role_ids = {user_role.RoleID for user_role in current_user.user_roles}
    if not (RoleID.ADMIN in user_role_ids or RoleID.MODERATOR in user_role_ids):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền cập nhật danh mục."
        )
    
    try:
        updated = category_crud.update(db, db_obj=category, obj_in=category_in)
        return updated
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# --- PROTECTED: Xóa category ---
@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int, 
    db: Session = Depends(deps.get_db), 
    current_user: User = Depends(deps.get_current_user)
):
    category = category_crud.get_by_id(db, category_id=category_id)
    if not category:
        return # Nếu không tìm thấy thì vẫn trả về 204 No Content

    user_role_ids = {user_role.RoleID for user_role in current_user.user_roles}
    if not (RoleID.ADMIN in user_role_ids or RoleID.MODERATOR in user_role_ids):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xóa danh mục."
        )
    
    category_crud.remove(db, id=category_id)
    return # Trả về 204 No Content