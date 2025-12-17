from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.models.sqlmodels import Category
from app.models import schemas

class CRUDCategory:
    def get_by_id(self, db: Session, category_id: int) -> Optional[Category]:
        """Lấy Category theo ID, chỉ lấy category chưa bị xóa."""
        return db.query(Category).filter(
            Category.CategoryID == category_id, 
            Category.IsDeleted == False
        ).first()

    def get_all(self, db: Session) -> List[Category]:
        """Lấy tất cả các Category chưa bị xóa."""
        # ĐÃ SỬA: Hàm get_all này sẽ được API endpoint công khai sử dụng.
        return db.query(Category).filter(Category.IsDeleted == False).all()

    def get_multiple(self, db: Session, skip: int = 0, limit: int = 100) -> List[Category]:
        """Lấy danh sách Category chưa bị xóa (có phân trang)."""
        return db.query(Category).filter(Category.IsDeleted == False).offset(skip).limit(limit).all()

    def get_by_name(self, db: Session, *, name: str) -> Optional[Category]:
        """Tìm Category theo tên."""
        return db.query(Category).filter(
            Category.CategoryName == name, 
            Category.IsDeleted == False
        ).first()

    def create(self, db: Session, obj_in: schemas.CategoryCreate) -> Category:
        """Tạo mới Category. Kiểm tra trùng tên trước khi thêm."""
        existing = self.get_by_name(db, name=obj_in.CategoryName)
        if existing:
            raise ValueError("Tên danh mục đã tồn tại.")
        db_category = Category(
            CategoryName=obj_in.CategoryName,
            IsDeleted=False,
            CreatedAt=datetime.utcnow(),
            UpdatedAt=datetime.utcnow()
        )
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        return db_category

    def update(self, db: Session, db_obj: Category, obj_in: schemas.CategoryUpdate) -> Category:
        """Cập nhật Category."""
        obj_data = obj_in.model_dump(exclude_unset=True)
        # Kiểm tra nếu đổi tên trùng với category khác
        if "CategoryName" in obj_data:
            name_conflict = db.query(Category).filter(
                Category.CategoryName == obj_data["CategoryName"],
                Category.CategoryID != db_obj.CategoryID,
                Category.IsDeleted == False
            ).first()
            if name_conflict:
                raise ValueError("Tên danh mục đã tồn tại.")
        
        for key, value in obj_data.items():
            setattr(db_obj, key, value)
            
        db_obj.UpdatedAt = datetime.utcnow()
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, id: int):
        """Soft delete: đánh dấu danh mục là đã xóa."""
        category = self.get_by_id(db, category_id=id)
        if not category:
            return None
        category.IsDeleted = True
        category.UpdatedAt = datetime.utcnow()
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

category_crud = CRUDCategory()