from sqlalchemy.orm import Session
from typing import List, Optional, Union
from datetime import datetime
from app.models.sqlmodels import Product, User, Category, ProductImage
from app.models import schemas
from app.core.constants import ProductStatus

class CRUDProductImage:
    """CRUD Operations cho ProductImage."""
    def create_with_product_id(
        self, db: Session, obj_in: schemas.ProductImageCreate, product_id: int
    ) -> ProductImage:
        # Chuyển đổi Pydantic model sang dictionary
        obj_data = obj_in.model_dump()
        db_obj = ProductImage(
            ProductID=product_id,
            IsDeleted=False,
            **obj_data
        )
        db.add(db_obj)
        # SỬA LỖI: Thay thế db.commit() bằng db.flush()
        # để ProductImage được thêm vào session nhưng chưa commit vĩnh viễn.
        db.flush() 
        db.refresh(db_obj)
        return db_obj

product_image_crud = CRUDProductImage()

class CRUDProduct:
    # ... (Các hàm get_by_id, get_multiple, get_by_title, get_available_products không thay đổi)

    def get_by_id(self, db: Session, product_id: int) -> Product | None:
        """Lấy sản phẩm theo ProductID, chỉ lấy sản phẩm chưa bị xóa."""
        return db.query(Product).filter(
            Product.ProductID == product_id, 
            Product.IsDeleted == False
        ).first()

    def get_multiple(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100, 
        status: Optional[Union[int, List[int]]] = ProductStatus.APPROVED # Hỗ trợ một int hoặc list of int
    ) -> List[Product]:
        """Lấy danh sách sản phẩm theo trạng thái (mặc định là Approved). 
           Nếu Status là None, lấy tất cả sản phẩm chưa bị xóa."""
        query = db.query(Product).filter(Product.IsDeleted == False)
        
        if status is not None:
            if isinstance(status, list):
                # Sử dụng 'in_' cho danh sách trạng thái
                query = query.filter(Product.Status.in_(status))
            elif isinstance(status, int):
                # Sử dụng so sánh bằng cho một trạng thái
                query = query.filter(Product.Status == status)
        
        return query.offset(skip).limit(limit).all()
    
    def create(self, db: Session, obj_in: schemas.ProductCreate, seller_id: int) -> Product:
        """Tạo sản phẩm mới."""
        obj_data = obj_in.model_dump()
        obj_data.pop("Status", None) 
        
        # Kiểm tra CategoryID hợp lệ
        category = db.query(Category).filter(
            Category.CategoryID == obj_data.get("CategoryID"), 
            Category.IsDeleted == False
        ).first()
        if not category:
            # Sửa lỗi: Nâng lỗi ValueError để tầng Service bắt
            raise ValueError("CategoryID không hợp lệ hoặc không tồn tại.")

        # Tạo mới sản phẩm
        db_product = Product(
            SellerID=seller_id,
            Status=ProductStatus.PENDING, 
            IsDeleted=False,
            ViewCount=0,
            **obj_data
        )
        db.add(db_product)
        # SỬA LỖI: Thay thế db.commit() bằng db.flush() để lấy ProductID
        db.flush() 
        db.refresh(db_product)
        return db_product

    def update(self, db: Session, db_obj: Product, obj_in: schemas.ProductUpdate) -> Product:
        """Cập nhật thông tin sản phẩm."""
        obj_data = obj_in.model_dump(exclude_unset=True)
        for key, value in obj_data.items():
            setattr(db_obj, key, value)
        db_obj.UpdatedAt = datetime.utcnow()
        db.add(db_obj)
        # SỬA LỖI: Update cũng không nên commit ở đây
        db.flush()
        db.refresh(db_obj)
        return db_obj

    # --- Phương thức Dọn dẹp (Nếu cần rollback thủ công) ---
    def remove(self, db: Session, product_id: int) -> Optional[Product]:
        """Xóa cứng sản phẩm (Chỉ dùng cho Rollback trong Service)."""
        # Khi dùng remove, ta cần chắc chắn rằng session chưa được commit.
        # Nếu đã commit rồi, cần gọi db.commit() sau khi xóa.
        obj = db.query(Product).get(product_id)
        if obj:
            db.delete(obj)
            return obj
        return None

    # Các phương thức khác... (soft_delete, increase_view_count không thay đổi)
    def soft_delete(self, db: Session, db_obj: Product) -> Product:
        db_obj.IsDeleted = True
        db_obj.UpdatedAt = datetime.utcnow()
        db.add(db_obj)
        db.commit() # Dùng commit vì đây là thao tác đơn lẻ
        db.refresh(db_obj)
        return db_obj
    
    def increase_view_count(self, db: Session, db_obj: Product) -> Product:
        db_obj.ViewCount += 1
        db.add(db_obj)
        db.commit() # Dùng commit vì đây là thao tác đơn lẻ
        db.refresh(db_obj)
        return db_obj

    # BỔ SUNG: HÀM CẬP NHẬT TRẠNG THÁI SẢN PHẨM CHO MODERATOR
    def update_status(self, db: Session, product_id: int, new_status: int) -> Optional[Product]:
        """Cập nhật trạng thái (Status) của sản phẩm theo ID."""
        product = self.get_by_id(db, product_id) # Dùng get_by_id để đảm bảo sản phẩm chưa bị xóa
        if product:
            product.Status = new_status
            product.UpdatedAt = datetime.utcnow() # Cập nhật thời gian
            db.add(product)
            db.commit() # Commit ngay vì đây là thao tác Moderator đơn lẻ
            db.refresh(product)
            return product
        return None

product_crud = CRUDProduct()