from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from datetime import datetime
# Import các models cần thiết
from app.models.sqlmodels import User, Role, UserRole, ShoppingCart 
from app.models import schemas # UserCreate, UserLogin, User, Role
from app.core.security import get_password_hash, create_random_key, verify_password # Giả định các hàm này tồn tại
from app.core.constants import DEFAULT_USER_ROLE_ID, RoleID # Giả định ID của Role 'User' là 3

class CRUDUser:

    def get_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """Lấy người dùng theo UserID, không lấy người dùng đã bị xóa."""
        return db.query(User).filter(
            User.UserID == user_id, 
            User.IsDeleted == False
        ).options(
            joinedload(User.user_roles).joinedload(UserRole.role) # Tải vai trò
        ).first()

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """Lấy người dùng theo Email (dùng cho đăng nhập và kiểm tra trùng lặp)."""
        return db.query(User).filter(
            User.Email == email, 
            User.IsDeleted == False
        ).options(
            joinedload(User.user_roles).joinedload(UserRole.role)
        ).first()

    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """Lấy người dùng theo Username."""
        return db.query(User).filter(
            User.Username == username, 
            User.IsDeleted == False
        ).options(
            joinedload(User.user_roles).joinedload(UserRole.role)
        ).first()

    def get_multiple(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Lấy danh sách người dùng (không bao gồm người dùng đã xóa)."""
        return db.query(User).filter(User.IsDeleted == False).offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: schemas.UserCreate) -> User:
        """Tạo người dùng mới, bao gồm mã hóa mật khẩu và gán vai trò."""
        
        random_key = create_random_key()
        hashed_password = get_password_hash(obj_in.Password, random_key)
        
        # 1. Tạo đối tượng User
        db_user = User(
            Username=obj_in.Username,
            Email=obj_in.Email,
            PasswordHash=hashed_password,
            RandomKey=random_key, # Lưu RandomKey để giải mã/kiểm tra
            FullName=obj_in.FullName,
            IsActive=True,
            IsDeleted=False
        )
        db.add(db_user)
        db.flush() # Flush để lấy UserID

        # 2. Gán Role mặc định (giả định là RoleID = 3 cho 'User')
        db_user_role = UserRole(
            UserID=db_user.UserID,
            RoleID=DEFAULT_USER_ROLE_ID 
        )
        db.add(db_user_role)
        
        # 3. Tạo Giỏ hàng (ShoppingCart) tương ứng (quan hệ 1:1)
        db_cart = ShoppingCart(
            UserID=db_user.UserID
        )
        db.add(db_cart)
        
        db.commit()
        db.refresh(db_user)
        return db_user
    
    def authenticate(self, db: Session, email: str, password: str) -> Optional[User]:
        """Xác thực người dùng bằng email và mật khẩu."""
        user = self.get_by_email(db, email=email)
        
        if not user:
            return None
        
        # Kiểm tra mật khẩu bằng cách dùng RandomKey
        if verify_password(password, user.PasswordHash, user.RandomKey):
            return user
        return None

    def update(self, db: Session, db_obj: User, obj_in: schemas.UserBase) -> User:
        """Cập nhật thông tin cơ bản của người dùng."""
        obj_data = obj_in.model_dump(exclude_unset=True)
        
        for key, value in obj_data.items():
            setattr(db_obj, key, value)
            
        db_obj.UpdatedAt = datetime.utcnow()
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def change_password(self, db: Session, db_obj: User, new_password: str) -> User:
        """Đổi mật khẩu cho người dùng."""
        new_random_key = create_random_key()
        db_obj.PasswordHash = get_password_hash(new_password, new_random_key)
        db_obj.RandomKey = new_random_key
        db_obj.UpdatedAt = datetime.utcnow()

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def create_moderator(self, db: Session, obj_in: schemas.UserCreate) -> User:
        """Tạo người dùng mới và gán vai trò Moderator (RoleID = 2)."""
        
        # Kiểm tra trùng lặp (nếu cần)
        if self.get_by_email(db, obj_in.Email) or self.get_by_username(db, obj_in.Username):
            raise ValueError("Email hoặc Username đã tồn tại.")

        random_key = create_random_key()
        # Sử dụng hàm get_password_hash đã có
        hashed_password = get_password_hash(obj_in.Password, random_key)
        
        # 1. Tạo đối tượng User
        db_user = User(
            Username=obj_in.Username,
            Email=obj_in.Email,
            PasswordHash=hashed_password,
            RandomKey=random_key,
            FullName=obj_in.FullName,
            IsActive=True, # Mặc định kích hoạt ngay
            IsDeleted=False
        )
        db.add(db_user)
        db.flush() # Flush để lấy UserID

        # 2. Gán Role là MODERATOR (RoleID = 2)
        # Sử dụng hằng số từ constants.py
        db_user_role = UserRole(
            UserID=db_user.UserID,
            RoleID= 2 # <--- ĐIỂM QUAN TRỌNG
        )
        db.add(db_user_role)
        
        # 3. Tạo Giỏ hàng (ShoppingCart) tương ứng
        db_cart = ShoppingCart(
            UserID=db_user.UserID
        )
        db.add(db_cart)
        
        db.commit()
        db.refresh(db_user)
        return db_user
user_crud = CRUDUser()