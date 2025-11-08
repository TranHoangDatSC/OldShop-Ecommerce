# F:\Document_Study\Semesters 2025-2026\Object-Oriented Analysis & Design\choDoCu-ecommerce-main\choDoCu-ecommerce-main\app\services\product_service.py

import os
import shutil
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session
# Thêm HTTPException và status
from fastapi import UploadFile, HTTPException, status 

from app.models import schemas
from app.models.sqlmodels import Product
from app.crud.crud_product import product_crud, product_image_crud 

STATIC_DIR = Path("static/images/products")
STATIC_DIR.mkdir(parents=True, exist_ok=True) 

class ProductService:
    def create_product_and_save_images(
        self, 
        db: Session,
        product_in: schemas.ProductCreate, 
        seller_id: int, 
        image_files: List[UploadFile]
    ) -> Product:
        
        # Biến để lưu trữ đường dẫn file đã lưu (để dọn dẹp nếu rollback)
        saved_file_paths: List[Path] = []
        new_product: Optional[Product] = None
        
        try:
            # 1. Tạo sản phẩm trong DB (Chỉ FLUSH, không COMMIT)
            new_product = product_crud.create(
                db=db,
                obj_in=product_in,
                seller_id=seller_id
            )
            product_id = new_product.ProductID
            
            # 2. Xử lý và lưu từng file ảnh
            for index, file in enumerate(image_files):
                file_ext = os.path.splitext(file.filename)[1]
                file_name_safe = f"product_{product_id}_{index}{file_ext}"
                file_path = STATIC_DIR / file_name_safe
                
                # 2a. Lưu file vào đĩa
                with file_path.open("wb") as buffer:
                    # file.file.seek(0) 
                    shutil.copyfileobj(file.file, buffer)
                
                # Lưu đường dẫn vật lý để dọn dẹp
                saved_file_paths.append(file_path) 
                
                # 2b. Tạo record ProductImage trong DB (Chỉ FLUSH, không COMMIT)
                image_url = f"/static/images/products/{file_name_safe}"
                image_record = schemas.ProductImageCreate(
                    ImageUrl=image_url,
                    IsDefault=(index == 0)
                )
                product_image_crud.create_with_product_id(
                    db=db,
                    obj_in=image_record,
                    product_id=product_id
                )
                
            # 3. COMMIT TẤT CẢ: Nếu mọi thứ thành công, COMMIT duy nhất 1 lần
            db.commit() 
            
            # 4. Refresh và trả về
            db.refresh(new_product) 
            return new_product

        except ValueError as e:
            # Lỗi nghiệp vụ (ví dụ: CategoryID không hợp lệ)
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
            
        except Exception as e:
            print(f"Lỗi xảy ra trong quá trình tạo sản phẩm: {e}")
            
            # SỬA LỖI: ROLLBACK DB trước
            db.rollback() 
            
            # Dọn dẹp File I/O (Chỉ xóa file đã lưu vật lý)
            for path in saved_file_paths:
                if path.exists():
                    os.remove(path)
                    
            # Nâng ngoại lệ HTTPException cho tầng API xử lý
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Lỗi hệ thống khi đăng sản phẩm: {e}"
            )

product_service = ProductService()