from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric, Text, SmallInteger, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from app.core.database import Base # Giả định Base được import

# Base = declarative_base() # Giả sử bạn sử dụng Base từ app.core.database

# --- Bảng User (CẬP NHẬT) ---
class User(Base):
    __tablename__ = "User"
    UserID = Column(Integer, primary_key=True, index=True)
    Username = Column(String(50), unique=True, nullable=False)
    Email = Column(String(100), unique=True, nullable=False)
    PasswordHash = Column(String(64), nullable=False)
    RandomKey = Column(String(32), unique=True, nullable=False) # Thêm UNIQUE
    FullName = Column(String(100), nullable=False) # Theo SQL, FullName là NOT NULL
    PhoneNumber = Column(String(15)) # Thêm PhoneNumber
    Address = Column(String(255)) # Thêm Address
    IsActive = Column(Boolean, default=True, nullable=False)
    IsDeleted = Column(Boolean, default=False, nullable=False)
    CreatedAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    UpdatedAt = Column(DateTime, onupdate=datetime.utcnow) # Thêm UpdatedAt
    
    user_roles = relationship("UserRole", back_populates="user")
    orders = relationship("Order", back_populates="buyer") # Cập nhật back_populates
    contacts = relationship("ContactInfo", back_populates="user")

# --- Bảng Role (CẬP NHẬT) ---
class Role(Base):
    __tablename__ = "Role"
    RoleID = Column(Integer, primary_key=True, index=True)
    RoleName = Column(String(50), unique=True, nullable=False)
    Description = Column(Text)
    IsDeleted = Column(Boolean, default=False, nullable=False) # Thêm IsDeleted
    CreatedAt = Column(DateTime, default=datetime.utcnow, nullable=False) # Thêm CreatedAt
    UpdatedAt = Column(DateTime, onupdate=datetime.utcnow) # Thêm UpdatedAt
    
    user_roles = relationship("UserRole", back_populates="role") # Thêm relationship

# --- Bảng UserRole (CẬP NHẬT) ---
class UserRole(Base):
    __tablename__ = "UserRole"
    # UserRoleID không có trong SQL, dùng Primary Key kép (UserID, RoleID)
    UserID = Column(Integer, ForeignKey("User.UserID"), primary_key=True, nullable=False) 
    RoleID = Column(Integer, ForeignKey("Role.RoleID"), primary_key=True, nullable=False)
    
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")

# --- Bảng Category (CẬP NHẬT) ---
class Category(Base):
    __tablename__ = "Category"
    CategoryID = Column(Integer, primary_key=True, index=True)
    CategoryName = Column(String(100), unique=True, nullable=False)
    Description = Column(Text)
    IsDeleted = Column(Boolean, default=False, nullable=False)
    CreatedAt = Column(DateTime, default=datetime.utcnow, nullable=False) # Thêm CreatedAt
    UpdatedAt = Column(DateTime, onupdate=datetime.utcnow) # Thêm UpdatedAt

# --- Bảng Product (CẬP NHẬT) ---
class Product(Base):
    __tablename__ = "Product"
    ProductID = Column(Integer, primary_key=True, index=True)
    SellerID = Column(Integer, ForeignKey("User.UserID"), nullable=False) 
    CategoryID = Column(Integer, ForeignKey("Category.CategoryID"), nullable=False) 
    Title = Column(String(255), nullable=False)
    Description = Column(Text)
    Price = Column(Numeric(18, 2), nullable=False)
    Quantity = Column(Integer, nullable=False)
    ViewCount = Column(Integer, default=0, nullable=False)
    VideoUrl = Column(String(500), nullable=False) # Theo SQL, Product có VideoUrl trực tiếp
    Status = Column(SmallInteger, default=0, nullable=False) 
    IsDeleted = Column(Boolean, default=False, nullable=False)
    CreatedAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    UpdatedAt = Column(DateTime, onupdate=datetime.utcnow) # Thêm UpdatedAt

    category = relationship("Category")
    seller = relationship("User", foreign_keys=[SellerID])
    images = relationship("ProductImage", back_populates="product")
    # videos relationship không cần thiết vì VideoUrl là cột trực tiếp

# --- Bảng ProductImage ---
class ProductImage(Base):
    __tablename__ = "ProductImage"
    ImageID = Column(Integer, primary_key=True, index=True)
    ProductID = Column(Integer, ForeignKey("Product.ProductID"), nullable=False)
    ImageUrl = Column(String(500), nullable=False)
    IsDefault = Column(Boolean, default=False, nullable=False)
    IsDeleted = Column(Boolean, default=False, nullable=False)
    
    product = relationship("Product", back_populates="images")

# --- Bảng PaymentMethod ---
class PaymentMethod(Base):
    __tablename__ = "PaymentMethod"
    PaymentMethodID = Column(Integer, primary_key=True, index=True)
    MethodName = Column(String(50), nullable=False, unique=True)
    IsOnline = Column(Boolean, nullable=False)
    IsDeleted = Column(Boolean, default=False, nullable=False)

# --- Bảng ContactInfo (Địa chỉ nhận hàng) ---
class ContactInfo(Base):
    __tablename__ = "ContactInfo"
    ContactID = Column(Integer, primary_key=True, index=True)
    UserID = Column(Integer, ForeignKey("User.UserID"), nullable=True) 
    RecipientName = Column(String(100), nullable=False)
    PhoneNumber = Column(String(15), nullable=False)
    StreetAddress = Column(String(255), nullable=False)
    City = Column(String(100))
    IsDeleted = Column(Boolean, default=False, nullable=False)
    
    user = relationship("User", back_populates="contacts", foreign_keys=[UserID]) # Thêm back_populates

# Cần thêm back_populates vào User
# User.contacts = relationship("ContactInfo", back_populates="user") 

# --- Bảng Order (CẬP NHẬT) ---
class Order(Base):
    __tablename__ = "Order"
    OrderID = Column(Integer, primary_key=True, index=True)
    BuyerID = Column(Integer, ForeignKey("User.UserID"), nullable=False)
    ContactID = Column(Integer, ForeignKey("ContactInfo.ContactID"), nullable=False)
    PaymentMethodID = Column(Integer, ForeignKey("PaymentMethod.PaymentMethodID"), nullable=False)
    OrderDate = Column(DateTime, default=datetime.utcnow, nullable=False)
    TotalAmount = Column(Numeric(18, 2), nullable=False)
    ShippingFee = Column(Numeric(18, 2), default=0)
    OrderStatus = Column(SmallInteger, default=0, nullable=False) 
    IsDeleted = Column(Boolean, default=False, nullable=False)

    buyer = relationship("User", foreign_keys=[BuyerID], back_populates="orders")
    contact = relationship("ContactInfo")
    payment_method = relationship("PaymentMethod")
    details = relationship("OrderDetail", back_populates="order") 

# --- Bảng OrderDetail ---
class OrderDetail(Base):
    __tablename__ = "OrderDetail"
    OrderDetailID = Column(Integer, primary_key=True, index=True)
    OrderID = Column(Integer, ForeignKey("Order.OrderID"), nullable=False)
    ProductID = Column(Integer, ForeignKey("Product.ProductID"), nullable=False)
    SellerID = Column(Integer, ForeignKey("User.UserID"), nullable=False)
    Price = Column(Numeric(18, 2), nullable=False) 
    Quantity = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="details")
    product = relationship("Product")
    seller = relationship("User", foreign_keys=[SellerID])

# --- Bảng ShoppingCart ---
class ShoppingCart(Base):
    __tablename__ = "ShoppingCart"
    CartID = Column(Integer, primary_key=True, index=True)
    UserID = Column(Integer, ForeignKey("User.UserID"), nullable=False, unique=True)
    LastUpdated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User")
    items = relationship("ShoppingCartItem", back_populates="cart")

# --- Bảng ShoppingCartItem ---
class ShoppingCartItem(Base):
    __tablename__ = "ShoppingCartItem"
    ItemID = Column(Integer, primary_key=True, index=True)
    CartID = Column(Integer, ForeignKey("ShoppingCart.CartID"), nullable=False)
    ProductID = Column(Integer, ForeignKey("Product.ProductID"), nullable=False)
    Quantity = Column(Integer, nullable=False)
    AddedDate = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('CartID', 'ProductID', name='uq_cart_product'), 
    )

    cart = relationship("ShoppingCart", back_populates="items")
    product = relationship("Product")

# --- Bảng MỚI: Transaction ---
class Transaction(Base):
    __tablename__ = "Transaction"
    TransactionID = Column(Integer, primary_key=True, index=True)
    OrderID = Column(Integer, ForeignKey("Order.OrderID"), nullable=False, unique=True) # UNIQUE 1:1
    PaymentMethodID = Column(Integer, ForeignKey("PaymentMethod.PaymentMethodID"), nullable=False)
    TransactionCode = Column(String(100))
    Amount = Column(Numeric(18, 2), nullable=False)
    TransactionStatus = Column(SmallInteger, nullable=False) # 0: Pending, 1: Success, 2: Failed, 3: Refund
    TransactionDate = Column(DateTime, default=datetime.utcnow, nullable=False)
    IsDeleted = Column(Boolean, default=False, nullable=False)
    
    order = relationship("Order")
    payment_method = relationship("PaymentMethod")

# --- Bảng MỚI: Review ---
class Review(Base):
    __tablename__ = "Review"
    ReviewID = Column(Integer, primary_key=True, index=True)
    ProductID = Column(Integer, ForeignKey("Product.ProductID"), nullable=False)
    BuyerID = Column(Integer, ForeignKey("User.UserID"), nullable=False)
    Rating = Column(SmallInteger, nullable=False) # Check (Rating BETWEEN 1 AND 5)
    Comment = Column(String(500))
    IsDeleted = Column(Boolean, default=False, nullable=False)
    CreatedAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        # Chỉ cho phép 1 review duy nhất từ 1 Buyer cho 1 Product
        UniqueConstraint('ProductID', 'BuyerID', name='UQ_Review_BuyerProduct'), 
    )
    
    product = relationship("Product")
    buyer = relationship("User")

# --- Bảng MỚI: ProductReviewLog ---
class ProductReviewLog(Base):
    __tablename__ = "ProductReviewLog"
    LogID = Column(Integer, primary_key=True, index=True)
    ProductID = Column(Integer, ForeignKey("Product.ProductID"), nullable=False)
    ReviewerID = Column(Integer, ForeignKey("User.UserID"), nullable=False)
    ActionType = Column(SmallInteger, nullable=False) # 1: Approval, 2: Reject, 3: Edit
    Notes = Column(String(500))
    ActionDate = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    product = relationship("Product")
    reviewer = relationship("User", foreign_keys=[ReviewerID])

# --- Bảng MỚI: SystemLog ---
class SystemLog(Base):
    __tablename__ = "SystemLog"
    LogID = Column(Integer, primary_key=True, index=True)
    UserID = Column(Integer, ForeignKey("User.UserID"), nullable=True) 
    ActionType = Column(String(50), nullable=False)
    TableName = Column(String(50))
    RecordID = Column(Integer)
    Description = Column(Text)
    LogTime = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    user = relationship("User")