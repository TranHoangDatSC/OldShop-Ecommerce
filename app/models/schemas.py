from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, EmailStr
from app.core.constants import ProductStatus

# --- SCHEMAS CHO ROLE ---
class RoleBase(BaseModel):
    RoleName: str
    Description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class Role(RoleBase):
    RoleID: int
    IsDeleted: bool
    CreatedAt: datetime
    UpdatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- SCHEMAS CHO USER ---
class UserBase(BaseModel):
    Email: EmailStr
    FullName: str # Theo SQL, FullName là NOT NULL
    PhoneNumber: Optional[str] = None
    Address: Optional[str] = None
    IsActive: Optional[bool] = True
    # IsAdmin không có trong SQL Model nhưng có thể được suy ra từ UserRole

class UserCreate(UserBase):
    Username: str
    Password: str
    class Config:
        min_anystr_length = 6
class UserUpdate(BaseModel):
    # UserID không cần ở đây vì nó sẽ nằm trong URL path
    Email: Optional[EmailStr] = None
    FullName: Optional[str] = None
    PhoneNumber: Optional[str] = None
    Address: Optional[str] = None
    
    # Không cho phép đổi Username trong phần này (hoặc có thể cho phép)
    # Tạm thời để Optional, nhưng thường Username là cố định.
    Username: Optional[str] = None 
    
    # Mật khẩu không bắt buộc khi cập nhật (để trống nếu không đổi)
    Password: Optional[str] = None 
    
    # Có thể dùng để kích hoạt/vô hiệu hóa tài khoản (optional)
    IsActive: Optional[bool] = None 
    
    class Config:
        min_anystr_length = 6 # Vẫn áp dụng cho Password nếu nó được cung cấp
        
class User(UserBase):
    UserID: int
    Username: str
    IsActive: bool
    IsDeleted: bool
    CreatedAt: datetime
    UpdatedAt: Optional[datetime] = None
    
    # Mối quan hệ: Bổ sung roles để hiển thị
    roles: List[Role] = [] 
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRoleBase(BaseModel):
    UserID: int
    RoleID: int

class UserRole(UserRoleBase):
    class Config:
        from_attributes = True

# --- SCHEMAS CHO TOKEN ---
class Token(BaseModel):
    access_token: str
    token_type: str
    roles: List[str] = []

class TokenData(BaseModel):
    sub: Optional[str] = None # UserID

# --- SCHEMAS CHO CATEGORY ---
class CategoryBase(BaseModel):
    CategoryName: str
    Description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass
class CategoryUpdate(CategoryBase):
    pass

class Category(CategoryBase):
    CategoryID: int
    IsDeleted: bool
    CreatedAt: datetime
    UpdatedAt: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# --- SCHEMAS CHO PRODUCT IMAGE ---
class ProductImageCreate(BaseModel):
    ImageUrl: str
    IsDefault: Optional[bool] = False

class ProductImage(ProductImageCreate):
    ImageID: int
    ProductID: int
    IsDeleted: bool

    class Config:
        from_attributes = True

# --- SCHEMAS CHO PRODUCT --- (Cập nhật dựa trên SQL)
class ProductBase(BaseModel):
    Title: str
    Description: Optional[str] = None
    Price: Decimal
    Quantity: int
    CategoryID: int
    VideoUrl: Optional[str] = None
    Status: int = ProductStatus.PENDING
    
class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    pass

class Product(ProductBase):
    ProductID: int
    SellerID: int
    ViewCount: int
    IsDeleted: bool
    CreatedAt: datetime
    UpdatedAt: Optional[datetime] = None
    
    PrimaryImageUrl: Optional[str] = None
    # Mối quan hệ: Thêm images
    images: List[ProductImage] = [] 
    
    class Config:
        from_attributes = True
        json_encoders = {Decimal: float}

# --- BỔ SUNG: SCHEMA CẬP NHẬT TRẠNG THÁI SẢN PHẨM ---
class ProductStatusUpdate(BaseModel):
    """Schema đơn giản dùng cho Moderator/Admin cập nhật trạng thái sản phẩm."""
    Status: int 

    @validator('Status')
    def validate_status(cls, value):
        # ✅ SỬA ĐỔI DƯỚI ĐÂY: Thêm ProductStatus.PENDING (giá trị 0)
        valid_statuses = [
            ProductStatus.PENDING.value,
            ProductStatus.APPROVED.value,
            ProductStatus.REJECTED.value
        ]
        
        if value not in valid_statuses:
            # Sửa thông báo lỗi cho phù hợp với 3 trạng thái
            raise ValueError(f'Trạng thái không hợp lệ. Phải là 0 (PENDING), 1 (APPROVED) hoặc 2 (REJECTED).')
        
        return value

# --- SCHEMAS CHO PAYMENT METHOD ---
class PaymentMethodBase(BaseModel):
    MethodName: str
    IsOnline: bool

class PaymentMethodCreate(PaymentMethodBase):
    pass

class PaymentMethod(PaymentMethodBase):
    PaymentMethodID: int
    IsDeleted: bool
    
    class Config:
        from_attributes = True

# --- SCHEMAS CHO CONTACT (Địa chỉ nhận hàng) ---
class ContactBase(BaseModel):
    RecipientName: str
    PhoneNumber: str
    StreetAddress: str
    City: Optional[str] = None

class ContactCreate(ContactBase):
    pass

class Contact(ContactBase):
    ContactID: int
    UserID: Optional[int] = None
    IsDeleted: bool
    
    class Config:
        from_attributes = True

# --- SCHEMAS CHO CART ITEM ---
class CartItemCreate(BaseModel):
    ProductID: int
    Quantity: int

class CartItem(CartItemCreate):
    ItemID: int
    CartID: int
    AddedDate: datetime
    
    class Config:
        from_attributes = True

# --- SCHEMAS CHO SHOPPING CART ---
class ShoppingCart(BaseModel):
    CartID: int
    UserID: int
    LastUpdated: datetime
    items: List[CartItem] = [] 

    class Config:
        from_attributes = True

# --- SCHEMAS CHO ORDER DETAIL ---
class OrderDetailBase(BaseModel):
    ProductID: int
    Quantity: int
    Price: Decimal # PriceAtOrder theo SQL là Price
    SellerID: int

class OrderDetailCreate(BaseModel):
    ProductID: int
    Quantity: int

class OrderDetail(OrderDetailBase):
    OrderDetailID: int
    OrderID: int
    
    class Config:
        from_attributes = True
        json_encoders = {Decimal: float}

# --- SCHEMAS CHO ORDER ---
class OrderCreate(BaseModel):
    # Yêu cầu ContactInfo (địa chỉ) và PaymentMethodID
    ContactInfo: ContactCreate 
    PaymentMethodID: int
    items: List[OrderDetailCreate] # Chi tiết sản phẩm

class Order(BaseModel):
    OrderID: int
    BuyerID: int
    ContactID: int
    PaymentMethodID: int
    TotalAmount: Decimal
    ShippingFee: Decimal
    OrderStatus: int
    OrderDate: datetime
    IsDeleted: bool
    details: List[OrderDetail] = [] # Mối quan hệ: Hiển thị chi tiết các mục trong đơn hàng

    class Config:
        from_attributes = True
        json_encoders = {Decimal: float}

# --- SCHEMAS CHO TRANSACTION ---
class TransactionBase(BaseModel):
    OrderID: int
    PaymentMethodID: int
    TransactionCode: Optional[str] = None
    Amount: Decimal
    TransactionStatus: int # 0: Pending, 1: Sucessfully, 2: Failed, 3: Refund

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    TransactionID: int
    TransactionDate: datetime
    IsDeleted: bool
    
    class Config:
        from_attributes = True
        json_encoders = {Decimal: float}

# --- SCHEMAS CHO REVIEW ---
class ReviewBase(BaseModel):
    Rating: int
    Comment: Optional[str] = None

class ReviewCreate(ReviewBase):
    ProductID: int

class Review(ReviewBase):
    ReviewID: int
    ProductID: int
    BuyerID: int
    IsDeleted: bool
    CreatedAt: datetime
    
    class Config:
        from_attributes = True

# --- SCHEMAS CHO PRODUCT REVIEW LOG ---
class ProductReviewLogBase(BaseModel):
    ProductID: int
    ReviewerID: int
    ActionType: int # 1: Approval, 2: Reject, 3: Edit
    Notes: Optional[str] = None

class ProductReviewLogCreate(ProductReviewLogBase):
    pass

class ProductReviewLog(ProductReviewLogBase):
    LogID: int
    ActionDate: datetime
    
    class Config:
        from_attributes = True

# --- SCHEMAS CHO SYSTEM LOG ---
class SystemLogBase(BaseModel):
    UserID: Optional[int] = None
    ActionType: str
    TableName: Optional[str] = None
    RecordID: Optional[int] = None
    Description: Optional[str] = None

class SystemLogCreate(SystemLogBase):
    pass

class SystemLog(SystemLogBase):
    LogID: int
    LogTime: datetime
    
    class Config:
        from_attributes = True