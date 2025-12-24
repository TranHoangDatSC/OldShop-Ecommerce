from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
# BỎ 'CartItem' ra khỏi dòng này vì file sqlmodels.py của bạn không có tên này
from app.models.sqlmodels import ContactInfo, Order, OrderDetail, Product, User 
from app.models import schemas

class CRUDOrder:
    def get_multi_by_user(self, db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Order]:
        return db.query(Order).filter(Order.UserID == user_id).offset(skip).limit(limit).all()

    def get_by_id(self, db: Session, order_id: int) -> Optional[Order]:
        return db.query(Order).options(joinedload(Order.details)).filter(Order.OrderID == order_id).first()

    def create_simple_order(self, db: Session, user_id: int, payment_method_id: int, items_in: List[schemas.OrderDetailCreate]) -> Order:
        user = db.query(User).filter(User.UserID == user_id).first()
        if not user:
            raise ValueError("Người dùng không tồn tại.")

        db_contact = ContactInfo(
            UserID=user_id,
            RecipientName=user.FullName or user.Username,
            PhoneNumber=user.PhoneNumber or "0000000000",
            StreetAddress=user.Address or "Chưa cập nhật địa chỉ",
            City="N/A"
        )
        db.add(db_contact)
        db.flush() 

        total_amount = 0
        order_details = []

        try:
            for item in items_in:
                product = db.query(Product).filter(Product.ProductID == item.ProductID).with_for_update().first()
                if not product or product.Quantity < item.Quantity:
                    # Lưu ý: db.rollback() ở đây sẽ hủy luôn cả db_contact phía trên, rất tốt.
                    raise ValueError(f"Sản phẩm {product.Title if product else item.ProductID} không đủ hàng.")

                total_amount += product.Price * item.Quantity
                product.Quantity -= item.Quantity
                
                order_details.append(OrderDetail(
                    ProductID=item.ProductID,
                    SellerID=product.SellerID,
                    Price=product.Price,
                    Quantity=item.Quantity
                ))

            db_order = Order(
                BuyerID=user_id,
                ContactID=db_contact.ContactID,
                PaymentMethodID=payment_method_id,
                TotalAmount=total_amount,
                ShippingFee=10000,
                OrderStatus=0 
            )
            db_order.details = order_details
            db.add(db_order)

            # TẠM THỜI CHƯA XÓA GIỎ HÀNG Ở ĐÂY ĐỂ TRÁNH LỖI IMPORT
            db.commit()
            db.refresh(db_order)
            return db_order

        except Exception as e:
            db.rollback()
            raise e

    def update_status(self, db: Session, order: Order, new_status: int) -> Order:
        order.OrderStatus = new_status
        db.add(order)
        db.commit()
        db.refresh(order)
        return order

order_crud = CRUDOrder()