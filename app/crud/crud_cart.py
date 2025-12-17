from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from app.models.sqlmodels import ShoppingCart, ShoppingCartItem, Product
from app.models import schemas
from app.core.constants import ProductStatus

class CRUDCart:
    def get_user_cart(self, db: Session, user_id: int) -> Optional[ShoppingCart]:
        cart = db.query(ShoppingCart).filter(ShoppingCart.UserID == user_id).options(joinedload(ShoppingCart.items)).first()
        if not cart:
            cart = self.create_cart(db, user_id)
        return cart

    def create_cart(self, db: Session, user_id: int) -> ShoppingCart:
        # Sử dụng datetime.utcnow() để đồng bộ với mặc định của SQLModel
        db_cart = ShoppingCart(
            UserID=user_id, 
            LastUpdated=datetime.utcnow() 
        )
        db.add(db_cart)
        db.commit()
        db.refresh(db_cart)
        return db_cart

    def get_item_by_product(self, db: Session, cart_id: int, product_id: int) -> Optional[ShoppingCartItem]:
        return db.query(ShoppingCartItem).filter(
            ShoppingCartItem.CartID == cart_id,
            ShoppingCartItem.ProductID == product_id
        ).first()

    def add_or_update_item(self, db: Session, user_id: int, item_in: schemas.CartItemCreate) -> ShoppingCart:
        cart = self.get_user_cart(db, user_id)
        
        # 1. Kiểm tra sản phẩm có hợp lệ không
        product = db.query(Product).filter(
            Product.ProductID == item_in.ProductID,
            Product.Status == ProductStatus.APPROVED,
            Product.IsDeleted == False
        ).first()
        
        if not product:
            raise ValueError("Sản phẩm không tồn tại hoặc không còn bán.")

        # 2. Tìm xem sản phẩm đã có trong giỏ chưa
        # Tìm xem sản phẩm đã có trong giỏ chưa
        cart_item = self.get_item_by_product(db, cart.CartID, item_in.ProductID)

        if cart_item:
            target_quantity = cart_item.Quantity + item_in.Quantity
            if target_quantity > product.Quantity:
                raise ValueError(f"Vượt quá kho.")
            cart_item.Quantity = target_quantity
            db.add(cart_item) # Lưu thay đổi của item
        else:
            db_item = ShoppingCartItem(
                CartID=cart.CartID,
                ProductID=item_in.ProductID,
                Quantity=item_in.Quantity,
                AddedDate=datetime.utcnow()
            )
            db.add(db_item) # Thêm item mới

        # Luôn cập nhật thời gian mới nhất cho giỏ hàng
        cart.LastUpdated = datetime.utcnow()
        db.add(cart) # Thêm dòng này để chắc chắn giỏ hàng được cập nhật LastUpdated
        
        db.commit()
        db.refresh(cart)
        return cart
    
    def remove_item(self, db: Session, user_id: int, product_id: int) -> ShoppingCart:
        cart = self.get_user_cart(db, user_id)
        cart_item = self.get_item_by_product(db, cart.CartID, product_id)
        if cart_item:
            db.delete(cart_item)
            db.commit()
            db.refresh(cart)
        return cart

    def clear_cart(self, db: Session, user_id: int) -> ShoppingCart:
        cart = self.get_user_cart(db, user_id)
        db.query(ShoppingCartItem).filter(ShoppingCartItem.CartID == cart.CartID).delete(synchronize_session=False)
        db.commit()
        db.refresh(cart)
        return cart
    
    def update_item_quantity(self, db: Session, user_id: int, product_id: int, new_qty: int) -> ShoppingCart:
        cart = self.get_user_cart(db, user_id)
        item = self.get_item_by_product(db, cart.CartID, product_id)
        
        if not item:
            raise HTTPException(status_code=404, detail="Sản phẩm không có trong giỏ.")
            
        # Kiểm tra tồn kho trước khi cập nhật
        product = db.query(Product).filter(Product.ProductID == product_id).first()
        if new_qty > product.Quantity:
            raise ValueError(f"Kho chỉ còn {product.Quantity} sản phẩm.")
            
        item.Quantity = new_qty
        db.add(item)
        db.commit()
        db.refresh(cart)
        return cart

cart_crud = CRUDCart()