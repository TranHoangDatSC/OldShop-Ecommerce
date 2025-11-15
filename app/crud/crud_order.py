from typing import List, Optional

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

# Giả sử bạn có các models Product, Order, OrderDetail trong sqlmodels
from app.models.sqlmodels import Order, OrderDetail, Product 
from app.models import schemas

# --- CRUDOrder ---

class CRUDOrder:
    
    def get_multi_by_user(
        self, 
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Order]:
        """Lấy danh sách các đơn hàng của một người dùng cụ thể."""
        return db.query(Order).filter(Order.UserID == user_id).offset(skip).limit(limit).all()

    def get_by_id(self, db: Session, order_id: int) -> Optional[Order]:
        """Lấy một đơn hàng theo ID, kèm theo chi tiết."""
        return db.query(Order).options(joinedload(Order.details)).filter(Order.OrderID == order_id).first()

    def create(self, db: Session, user_id: int, obj_in: schemas.OrderCreate) -> Order:
        """Tạo đơn hàng mới, tính toán tổng tiền và tạo chi tiết đơn hàng."""
        
        total_amount = 0
        order_details_list = []

        # 1. Lấy thông tin giá sản phẩm
        product_ids = [item.ProductID for item in obj_in.items]
        products = db.query(Product).filter(Product.ProductID.in_(product_ids)).all()
        product_map = {p.ProductID: p for p in products}

        # 2. Xử lý từng item
        for item in obj_in.items:
            product = product_map.get(item.ProductID)
            if not product:
                raise ValueError(f"Product ID {item.ProductID} not found.")
            
            # Kiểm tra tồn kho (Logic đơn giản)
            if product.StockQuantity < item.Quantity:
                raise ValueError(f"Not enough stock for Product ID {item.ProductID}.")

            price_at_order = product.Price
            subtotal = price_at_order * item.Quantity
            total_amount += subtotal
            
            # Giảm tồn kho (Rất quan trọng)
            product.StockQuantity -= item.Quantity
            db.add(product)
            
            order_details_list.append(
                OrderDetail(
                    ProductID=item.ProductID,
                    Quantity=item.Quantity,
                    PriceAtOrder=price_at_order
                )
            )

        # 3. Tạo đối tượng Order
        db_order = Order(
            UserID=user_id,
            TotalAmount=total_amount,
            ShippingAddress=obj_in.ShippingAddress,
            OrderStatus='Pending' 
        )

        # 4. Gắn chi tiết và lưu DB
        db_order.details = order_details_list
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        return db_order

    def update_status(self, db: Session, order: Order, new_status: str) -> Order:
        """Cập nhật trạng thái của đơn hàng."""
        order.Status = new_status
        db.add(order)
        db.commit()
        db.refresh(order)
        return order
    
order_crud = CRUDOrder()