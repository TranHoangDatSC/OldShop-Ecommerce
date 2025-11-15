from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api import deps
from app.models import schemas
from app.models.sqlmodels import Category, User
from app.crud.crud_category import category_crud
from app.core.constants import RoleID
from app.core import database
from app.models import sqlmodels

router = APIRouter()

# --- PUBLIC: Lấy danh sách category ---
@router.get("/", response_model=List[schemas.Category])
def get_categories(db: Session = Depends(get_db)):
    return db.query(sqlmodels.Category).all()

def read_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    categories = category_crud.get_multiple(db, skip=skip, limit=limit)
    return categories


# --- PUBLIC: Lấy chi tiết category ---
@router.get("/{category_id}", response_model=schemas.Category)
def read_category(
    category_id: int,
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    # Chỉ ADMIN hoặc MODERATOR mới được tạo
    user_role_ids = {user_role.RoleID for user_role in current_user.user_roles}
    if not (RoleID.ADMIN in user_role_ids or RoleID.MODERATOR in user_role_ids):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền tạo danh mục mới."
        )

    new_category = category_crud.create(db, obj_in=category_in)
    return new_category


# --- PROTECTED: Cập nhật category ---
@router.put("/{category_id}", response_model=schemas.Category)
def update_category(
    category_id: int,
    category_in: schemas.CategoryUpdate,
    db: Session = Depends(get_db),
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

    updated = category_crud.update(db, db_obj=category, obj_in=category_in)
    return updated


# --- PROTECTED: Xóa category ---
@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    category = category_crud.get_by_id(db, category_id=category_id)
    if not category:
        return

    user_role_ids = {user_role.RoleID for user_role in current_user.user_roles}
    if not (RoleID.ADMIN in user_role_ids or RoleID.MODERATOR in user_role_ids):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xóa danh mục."
        )

    category_crud.remove(db, id=category_id)
    return
