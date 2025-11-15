from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import Any, List, Optional

from app.core.database import get_db
from app.api import deps
from app.models import schemas, sqlmodels
from app.models.sqlmodels import Product, User
from app.crud.crud_product import product_crud
from app.core.constants import ProductStatus, RoleID
from app.services.product_service import attach_product_response_fields, product_service

router = APIRouter()

# --- Endpoint Public: Xem danh sách sản phẩm ---

@router.get("/", response_model=List[schemas.Product])
def read_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    products = product_crud.get_multiple(
        db, skip=skip, limit=limit, status=ProductStatus.APPROVED
    )
    return products

# --- Endpoint Public: Xem chi tiết sản phẩm ---
@router.get("/{product_id}", response_model=schemas.Product)
def read_product_detail(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = product_crud.get_by_id(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sản phẩm không tồn tại hoặc đã bị xóa."
        )
    
    # SỬ DỤNG HÀM HELPER để thêm PrimaryImageUrl
    product_out = attach_product_response_fields(product) 
    
    return product_out

# --- Endpoint Protected: Tạo sản phẩm mới (chỉ JSON) ---
@router.post("/", response_model=schemas.Product, status_code=status.HTTP_201_CREATED)
def create_product(
    product_in: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    try:
        # Gọi crud tạo sản phẩm, truyền model Pydantic chứ không phải dict
        new_product = product_crud.create(
            db=db,
            obj_in=product_in,
            seller_id=current_user.UserID
        )
        return new_product
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# --- Endpoint Public: Xem chi tiết sản phẩm ---
@router.get("/{product_id}", response_model=schemas.Product)
def read_product_detail(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = product_crud.get_by_id(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sản phẩm không tồn tại hoặc đã bị xóa."
        )
    return product


# --- Endpoint Protected: Cập nhật sản phẩm ---

@router.put("/{product_id}", response_model=schemas.Product)
def update_product(
    product_id: int,
    product_in: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    product = product_crud.get_by_id(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sản phẩm không tồn tại."
        )

    # Kiểm tra quyền người dùng
    user_role_ids = {user_role.RoleID for user_role in current_user.user_roles}
    is_admin_or_moderator = (
        RoleID.ADMIN in user_role_ids or RoleID.MODERATOR in user_role_ids
    )

    if product.SellerID != current_user.UserID and not is_admin_or_moderator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền cập nhật sản phẩm này."
        )

    try:
        updated_product = product_crud.update(db, db_obj=product, obj_in=product_in)
        return updated_product
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Lỗi khi cập nhật: {e}"
        )
    
# --- Endpoint Protected: Tạo sản phẩm mới VỚI ẢNH (ĐÃ KÍCH HOẠT) ---
@router.post("/upload", response_model=schemas.Product, status_code=status.HTTP_201_CREATED)
def create_product_with_images(
    # Nhận các trường text bằng Form()
    title: str = Form(...),
    description: Optional[str] = Form(None),
    price: Decimal = Form(...),
    quantity: int = Form(...),
    category_id: int = Form(...),
    video_url: Optional[str] = Form(None),
    # Nhận files
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    if len(files) == 0 or len(files) > 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cần tải lên từ 1 đến 3 ảnh."
        )

    # 1. Tạo Pydantic model từ Form data
    product_data = schemas.ProductCreate(
        Title=title,
        Description=description,
        Price=price,
        Quantity=quantity,
        CategoryID=category_id,
        VideoUrl=video_url
    )
    
    try:
        # 2. Gọi tầng Service để xử lý cả DB và File I/O
        new_product = product_service.create_product_and_save_images(
            db=db,
            product_in=product_data,
            seller_id=current_user.UserID,
            image_files=files
        )
        
        return new_product
    
    except ValueError as e:
        # Bắt lỗi từ CRUD (ví dụ: CategoryID không hợp lệ)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Bắt lỗi chung từ Service (ví dụ: lỗi lưu file)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi hệ thống khi đăng sản phẩm: {e}"
        )

# --- Endpoint Protected: Xóa sản phẩm (Soft Delete) ---
@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    product = product_crud.get_by_id(db, product_id=product_id)
    if not product:
        return

    user_role_ids = {user_role.RoleID for user_role in current_user.user_roles}
    is_admin_or_moderator = (
        RoleID.ADMIN in user_role_ids or RoleID.MODERATOR in user_role_ids
    )

    if product.SellerID != current_user.UserID and not is_admin_or_moderator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xóa sản phẩm này."
        )

    if not product.IsDeleted:
        product.IsDeleted = True
        db.add(product)
        db.commit()

    return

# ----------------------------------------------------------------------------------
# BỔ SUNG: API LẤY DANH SÁCH SẢN PHẨM CHO MODERATOR (PENDING + APPROVED)
# ----------------------------------------------------------------------------------
@router.get("/moderator/all", response_model=List[schemas.Product])
def read_moderator_products(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Any:

    # 2. Lấy danh sách sản phẩm đang chờ duyệt (0) và đã duyệt (1)
    products = product_crud.get_multiple(
        db, 
        status=[ProductStatus.PENDING, ProductStatus.APPROVED], # Lấy cả 2 trạng thái
        skip=skip, 
        limit=limit
    )
    return products

# ----------------------------------------------------
# BỔ SUNG: API CẬP NHẬT TRẠNG THÁI CHO MODERATOR/ADMIN 
# ----------------------------------------------------
@router.put("/status/{product_id}", response_model=schemas.Product)
def update_product_status(
    *,
    db: Session = Depends(get_db),
    product_id: int,
    status_update: schemas.ProductStatusUpdate,
) -> Any:
    
    product = product_crud.get_by_id(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sản phẩm không tồn tại hoặc đã bị xóa."
        )

    # 3. Cập nhật trạng thái
    updated_product = product_crud.update_status(
        db=db,
        product_id=product_id,
        new_status=status_update.Status 
    )

    if not updated_product:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể cập nhật trạng thái sản phẩm."
        )
    return updated_product

# ----------------------------------------------------
# Endpoint Cũ: API LẤY DANH SÁCH SẢN PHẨM CHỜ DUYỆT (Giữ lại nếu có UI khác dùng)
# ----------------------------------------------------
@router.get("/pending", response_model=List[schemas.Product])
def read_pending_products(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """ [MODERATOR/ADMIN ONLY] Lấy danh sách sản phẩm đang chờ duyệt (Status = 0). """
    products = product_crud.get_multiple(
        db, 
        status=ProductStatus.PENDING, 
        skip=skip, 
        limit=limit
    )
    return products