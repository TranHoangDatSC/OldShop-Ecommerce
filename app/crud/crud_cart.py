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
        db_cart = ShoppingCart(UserID=user_id)
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
        
        product = db.query(Product).filter(
            Product.ProductID == item_in.ProductID, 
            Product.Status == ProductStatus.APPROVED, 
            Product.IsDeleted == False
        ).first()
        
        if not product:
            raise ValueError("Sản phẩm không tồn tại hoặc không còn bán.")
            
        if item_in.Quantity <= 0 or item_in.Quantity > product.Quantity:
            raise ValueError(f"Số lượng không hợp lệ. Tối đa là {product.Quantity}.")

        cart_item = self.get_item_by_product(db, cart.CartID, item_in.ProductID)
        
        if cart_item:
            cart_item.Quantity = item_in.Quantity
            db.add(cart_item)
        else:
            db_item = ShoppingCartItem(
                CartID=cart.CartID,
                ProductID=item_in.ProductID,
                Quantity=item_in.Quantity
            )
            db.add(db_item)
            
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
        
cart_crud = CRUDCart()