from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from app.api import deps
from app.core.database import get_db
from app.models import schemas, sqlmodels
from app.crud.crud_cart import cart_crud

router = APIRouter()

@router.get("/", response_model=schemas.ShoppingCartOut)
def get_cart(
    db: Session = Depends(get_db),
    current_user: sqlmodels.User = Depends(deps.get_current_user)
) -> Any:
    """
    Lấy toàn bộ giỏ hàng của người dùng hiện tại.
    """
    return cart_crud.get_user_cart(db, user_id=current_user.UserID)

@router.post("/add", response_model=schemas.ShoppingCartOut)
def add_to_cart(
    *,
    db: Session = Depends(get_db),
    item_in: schemas.CartItemCreate,
    current_user: sqlmodels.User = Depends(deps.get_current_user)
) -> Any:
    """
    Thêm sản phẩm vào giỏ hàng. Nếu sản phẩm đã tồn tại thì cộng dồn số lượng.
    """
    try:
        cart = cart_crud.add_or_update_item(
            db, user_id=current_user.UserID, item_in=item_in
        )
        return cart
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/remove/{product_id}", response_model=schemas.ShoppingCartOut)
def remove_from_cart(
    *,
    db: Session = Depends(get_db),
    product_id: int,
    current_user: sqlmodels.User = Depends(deps.get_current_user)
) -> Any:
    """
    Xóa một loại sản phẩm khỏi giỏ hàng.
    """
    return cart_crud.remove_item(db, user_id=current_user.UserID, product_id=product_id)

@router.delete("/clear", response_model=schemas.ShoppingCartOut)
def clear_cart(
    db: Session = Depends(get_db),
    current_user: sqlmodels.User = Depends(deps.get_current_user)
) -> Any:
    """
    Xóa sạch giỏ hàng của người dùng.
    """
    return cart_crud.clear_cart(db, user_id=current_user.UserID)

@router.put("/update", response_model=schemas.ShoppingCartOut)
def update_cart_item(
    *,
    db: Session = Depends(get_db),
    item_in: schemas.CartItemUpdate, # Nhận { "ProductID": int, "new_quantity": int }
    current_user: sqlmodels.User = Depends(deps.get_current_user)
):
    # Bạn cần cập nhật crud_cart.py để có hàm update_item_quantity
    cart = cart_crud.update_item_quantity(
        db, 
        user_id=current_user.UserID, 
        product_id=item_in.ProductID, 
        new_qty=item_in.new_quantity
    )
    return cart