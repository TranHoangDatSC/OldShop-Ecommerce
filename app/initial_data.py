from sqlalchemy.orm import Session
from app.models.sqlmodels import Role, Category, User, UserRole, PaymentMethod
from app.core import security 
from datetime import datetime
from app.core.constants import RoleID # Sử dụng constant

# --- Dữ liệu mẫu ---
ROLES_DATA = [
    {"RoleID": RoleID.ADMIN, "RoleName": "Admin", "Description": "Quản trị hệ thống, có toàn quyền."},
    {"RoleID": RoleID.MODERATOR, "RoleName": "Moderator", "Description": "Người kiểm duyệt sản phẩm sản phẩm."},
    {"RoleID": RoleID.CUSTOMER, "RoleName": "Customer", "Description": "Khách hàng thông thường, có thể mua hàng lẫn bán hàng."},
]

CATEGORIES_DATA = [
    {"CategoryID": 1, "CategoryName": "Đồ điện tử", "Description": "Thiết bị điện tử, điện thoại, máy tính..."},
    {"CategoryID": 2, "CategoryName": "Thời trang", "Description": "Quần áo, giày dép, phụ kiện..."},
    {"CategoryID": 3, "CategoryName": "Đồ gia dụng", "Description": "Bàn ghế, nồi cơm điện..."},
    {"CategoryID": 4, "CategoryName": "Trang trí", "Description": "Chậu cây, hồ cá..."},
]

PAYMENT_METHODS_DATA = [
    {"PaymentMethodID": 1, "MethodName": "COD", "IsOnline": False},
    {"PaymentMethodID": 2, "MethodName": "VNPAY", "IsOnline": True},
    {"PaymentMethodID": 3, "MethodName": "MOMO", "IsOnline": True},
    {"PaymentMethodID": 4, "MethodName": "PAYPAL", "IsOnline": True}
]

# --- Hàm Seeder ---
def init_db(db: Session) -> None:
    print("Bắt đầu khởi tạo dữ liệu mẫu...")
    
    # 1. Seed Roles
    for role_data in ROLES_DATA:
        role = db.query(Role).filter(Role.RoleID == role_data["RoleID"]).first()
        if not role:
            db_role = Role(**role_data)
            db.add(db_role)
    
    # 2. Seed Categories
    for cat_data in CATEGORIES_DATA:
        category = db.query(Category).filter(Category.CategoryID == cat_data["CategoryID"]).first()
        if not category:
            db_cat = Category(**cat_data)
            db.add(db_cat)

    # 3. Seed Payment Methods
    for method_data in PAYMENT_METHODS_DATA:
        method = db.query(PaymentMethod).filter(PaymentMethod.PaymentMethodID == method_data["PaymentMethodID"]).first()
        if not method:
            db_method = PaymentMethod(**method_data)
            db.add(db_method)
    
    db.commit()

    # 4. Seed Admin User 
    admin_email = "admin@oldshop.com"
    user_admin = db.query(User).filter(User.Email == admin_email).first()

    if not user_admin:
        print("Tạo tài khoản Admin mẫu...")
        
        admin_random_key = security.generate_random_key(32)
        admin_hashed_password = security.get_password_hash("adminpass", admin_random_key)
        
        db_user = User(
            Username="admin",
            Email=admin_email,
            PasswordHash=admin_hashed_password,
            RandomKey=admin_random_key,
            FullName="OldShop Administrator",
            IsActive=True,
            CreatedAt=datetime.utcnow()
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        admin_role = db.query(Role).filter(Role.RoleID == RoleID.ADMIN).first()
        if admin_role:
            db_user_role = UserRole(
                UserID=db_user.UserID, 
                RoleID=admin_role.RoleID
            )
            db.add(db_user_role)
            db.commit()
            print(f"Admin User '{admin_email}' được tạo với mật khẩu 'adminpass'.")
            
    else:
        print("Admin User đã tồn tại, bỏ qua tạo mới.")

    print("Hoàn thành khởi tạo dữ liệu mẫu.")