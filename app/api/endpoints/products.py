from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from app.core.database import get_db
from app.api import deps
from app.models import schemas, sqlmodels
from app.models.sqlmodels import User
from app.crud.crud_product import product_crud
from app.core.constants import ProductStatus, RoleID
from app.services.product_service import attach_product_response_fields, product_service

router = APIRouter()

# --- Endpoint Public: Xem danh sách sản phẩm (Bắt buộc dùng Service để đính kèm ảnh) ---
@router.get("/", response_model=List[schemas.Product])
def read_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    # CHÚ Ý: Cần dùng product_service.get_products_with_primary_image 
    # Thay vì product_crud.get_multiple để đảm bảo PrimaryImageUrl được đính kèm.
    products = product_service.get_products_with_primary_image(
        db, 
        skip=skip, 
        limit=limit, 
        status=ProductStatus.APPROVED
    )
    return products

# --- Endpoint Public: Xem chi tiết sản phẩm (Đã sửa lỗi trùng lặp và dùng hàm đính kèm ảnh) ---
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

# --- Endpoint Protected: Tạo sản phẩm mới (chỉ JSON, KHÔNG dùng ảnh) ---
# Tạm thời giữ lại nếu có giao diện dùng JSON, nhưng nên dùng /upload
@router.post("/", response_model=schemas.Product, status_code=status.HTTP_201_CREATED)
def create_product(
    product_in: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    try:
        new_product = product_crud.create(
            db=db,
            obj_in=product_in,
            seller_id=current_user.UserID
        )
        return attach_product_response_fields(new_product) # Đính kèm ảnh sau khi tạo
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

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
    print(f"--- DEBUG QUYỀN ---")
    print(f"ID Sản phẩm thuộc về Seller: {product.SellerID}")
    print(f"ID Bạn đang đăng nhập là: {current_user.UserID}")

    if product.SellerID != current_user.UserID and not is_admin_or_moderator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền cập nhật sản phẩm này."
        )
    
    try:
        updated_product = product_crud.update(db, db_obj=product, obj_in=product_in)
        return attach_product_response_fields(updated_product) # Đính kèm ảnh sau khi cập nhật
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Lỗi khi cập nhật: {e}"
        )

# --- Endpoint Protected: Tạo sản phẩm mới VỚI ẢNH ---
@router.post("/upload", response_model=schemas.Product, status_code=status.HTTP_201_CREATED)
def create_product_with_images(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    price: Decimal = Form(...),
    quantity: int = Form(...),
    category_id: int = Form(...),
    video_url: Optional[str] = Form(None),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    if len(files) == 0 or len(files) > 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cần tải lên từ 1 đến 3 ảnh."
        )

    product_data = schemas.ProductCreate(
        Title=title,
        Description=description,
        Price=price,
        Quantity=quantity,
        CategoryID=category_id,
        VideoUrl=video_url
    )
    
    try:
        new_product = product_service.create_product_and_save_images(
            db=db,
            product_in=product_data,
            seller_id=current_user.UserID,
            image_files=files
        )
        return new_product
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        # Nếu product_service đã raise HTTPException (ví dụ: lỗi lưu file) thì ném lại
        raise
    except Exception as e:
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
        product_crud.soft_delete(db, db_obj=product) # Dùng hàm soft_delete đã commit
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
    # Lấy danh sách sản phẩm đang chờ duyệt (0) và đã duyệt (1)
    products = product_service.get_products_with_primary_image(
        db, 
        status=[ProductStatus.PENDING, ProductStatus.APPROVED], 
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

    # Cập nhật trạng thái
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
    
    return attach_product_response_fields(updated_product)
# ----------------------------------------------------------------------------------
# Endpoint Cũ: API LẤY DANH SÁCH SẢN PHẨM CHỜ DUYỆT (Chuyển sang dùng service)
# ----------------------------------------------------------------------------------
@router.get("/pending", response_model=List[schemas.Product])
def read_pending_products(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Any:
    products = product_service.get_products_with_primary_image(
        db, 
        status=ProductStatus.PENDING, 
        skip=skip, 
        limit=limit
    )
    return products