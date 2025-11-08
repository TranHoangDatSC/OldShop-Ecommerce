IF NOT EXISTS (
    SELECT name
    FROM sys.databases
    WHERE
        name = N'OldShop'
) BEGIN
CREATE DATABASE OldShop;

END

USE OldShop;
GO

-- 1. Role
CREATE TABLE Role (
    RoleID INT PRIMARY KEY IDENTITY (1, 1),
    RoleName NVARCHAR (50) NOT NULL UNIQUE, --'Admin', 'Reviewer', 'User'
    Description NVARCHAR (255),
    IsDeleted BIT NOT NULL DEFAULT 0,
    CreatedAt DATETIME NOT NULL DEFAULT GETDATE (),
    UpdatedAt DATETIME
);
GO

-- 2. User
CREATE TABLE [User] (
    UserID INT PRIMARY KEY IDENTITY(1,1),
    Username VARCHAR(50) NOT NULL UNIQUE,
    Email VARCHAR(100) NOT NULL UNIQUE,
    PasswordHash CHAR(64) NOT NULL,     -- SHA-256 Hash
    RandomKey CHAR(32) NOT NULL UNIQUE, -- Use for hash password
    FullName NVARCHAR(100) NOT NULL,
    PhoneNumber VARCHAR(15),
    Address NVARCHAR(255),
    IsActive BIT NOT NULL DEFAULT 1,    -- Status: Lock/Unlock
    IsDeleted BIT NOT NULL DEFAULT 0,
    CreatedAt DATETIME NOT NULL DEFAULT GETDATE(),
    UpdatedAt DATETIME
);
GO

-- 3. UserRole (Junction)
CREATE TABLE UserRole (
    UserID INT NOT NULL,
    RoleID INT NOT NULL,
    PRIMARY KEY (UserID, RoleID),
    FOREIGN KEY (UserID) REFERENCES [User](UserID),
    FOREIGN KEY (RoleID) REFERENCES Role(RoleID)
);
GO

-- 4. Category
CREATE TABLE Category (
    CategoryID INT PRIMARY KEY IDENTITY (1, 1),
    CategoryName NVARCHAR (100) NOT NULL UNIQUE,
    Description NVARCHAR (255),
    IsDeleted BIT NOT NULL DEFAULT 0,
    CreatedAt DATETIME NOT NULL DEFAULT GETDATE (),
    UpdatedAt DATETIME
);
GO

-- 5. Product
CREATE TABLE Product (
    ProductID INT PRIMARY KEY IDENTITY(1,1),
    SellerID INT NOT NULL,              -- The seller
    CategoryID INT NOT NULL,            -- Category
    Title NVARCHAR(255) NOT NULL,
    Description NVARCHAR(MAX),
    Price DECIMAL(18, 2) NOT NULL CHECK (Price >= 0),
    Quantity INT NOT NULL CHECK (Quantity >= 0),
    ViewCount INT NOT NULL DEFAULT 0,
    VideoUrl VARCHAR(500) NOT NULL,
    Status TINYINT NOT NULL DEFAULT 0,  -- 0: Pending, 1: Approved/Posted, 2: Discontinued/Out of stock
    IsDeleted BIT NOT NULL DEFAULT 0,
    CreatedAt DATETIME NOT NULL DEFAULT GETDATE(),
    UpdatedAt DATETIME,
    FOREIGN KEY (SellerID) REFERENCES [User](UserID),
    FOREIGN KEY (CategoryID) REFERENCES Category(CategoryID)
);
GO

-- 6. ProductImage (Weak Entity)
CREATE TABLE ProductImage (
    ImageID INT PRIMARY KEY IDENTITY (1, 1),
    ProductID INT NOT NULL,
    ImageUrl VARCHAR(500) NOT NULL,
    IsDefault BIT NOT NULL DEFAULT 0,
    IsDeleted BIT NOT NULL DEFAULT 0,
    FOREIGN KEY (ProductID) REFERENCES Product (ProductID)
);
GO

-- 7. PaymentMethod
CREATE TABLE PaymentMethod (
    PaymentMethodID INT PRIMARY KEY IDENTITY (1, 1),
    MethodName NVARCHAR (50) NOT NULL UNIQUE, -- Ex: 'COD', 'VNPAY', 'MOMO', 'PAYPAL'
    IsOnline BIT NOT NULL, -- 1: Online, 0: Offline (COD)
    IsDeleted BIT NOT NULL DEFAULT 0
);
GO

-- 8. ContactInfo
CREATE TABLE ContactInfo (
    ContactID INT PRIMARY KEY IDENTITY(1,1),
    UserID INT,                              -- If this contact linked to user
    RecipientName NVARCHAR(100) NOT NULL,
    PhoneNumber VARCHAR(15) NOT NULL,
    StreetAddress NVARCHAR(255) NOT NULL,
    City NVARCHAR(100),
    IsDeleted BIT NOT NULL DEFAULT 0,
    FOREIGN KEY (UserID) REFERENCES [User](UserID)
);
GO

-- 9. Order
CREATE TABLE [Order] (
    OrderID INT PRIMARY KEY IDENTITY(1,1),
    BuyerID INT NOT NULL,                       -- Buyer
    ContactID INT NOT NULL,                     -- Delivery address
    PaymentMethodID INT NOT NULL,
    OrderDate DATETIME NOT NULL DEFAULT GETDATE(),
    TotalAmount DECIMAL(18, 2) NOT NULL,
    ShippingFee DECIMAL(18, 2) DEFAULT 0,
    OrderStatus TINYINT NOT NULL DEFAULT 0,     -- 0: Pending, 1: Approved, 2: Delivering, 3: Finish, 4: Cancel
    IsDeleted BIT NOT NULL DEFAULT 0,
    FOREIGN KEY (BuyerID) REFERENCES [User](UserID),
    FOREIGN KEY (ContactID) REFERENCES ContactInfo(ContactID),
    FOREIGN KEY (PaymentMethodID) REFERENCES PaymentMethod(PaymentMethodID)
);
GO

-- 10. OrderDetail (Weak Entity)
CREATE TABLE OrderDetail (
    OrderDetailID INT PRIMARY KEY IDENTITY(1,1),
    OrderID INT NOT NULL,
    ProductID INT NOT NULL,
    SellerID INT NOT NULL,         -- Check seller     
    Price DECIMAL(18, 2) NOT NULL, -- Price at time order
    Quantity INT NOT NULL CHECK (Quantity > 0),
    FOREIGN KEY (OrderID) REFERENCES [Order](OrderID),
    FOREIGN KEY (ProductID) REFERENCES Product(ProductID),
    FOREIGN KEY (SellerID) REFERENCES [User](UserID)
);
GO

-- 11. Transaction (Weak Entity, 1:1)
CREATE TABLE [Transaction] (
    TransactionID INT PRIMARY KEY IDENTITY(1,1),
    OrderID INT NOT NULL UNIQUE,        -- Transaction linked to order (Constraint 1:1)
    PaymentMethodID INT NOT NULL,
    TransactionCode VARCHAR(100),       -- TransactionID (VNPAY, MOMO)
    Amount DECIMAL(18, 2) NOT NULL,
    TransactionStatus TINYINT NOT NULL, -- 0: Pending, 1: Sucessfully, 2: Failed, 3: Refund
    TransactionDate DATETIME NOT NULL DEFAULT GETDATE(),
    IsDeleted BIT NOT NULL DEFAULT 0,
    FOREIGN KEY (OrderID) REFERENCES [Order](OrderID),
    FOREIGN KEY (PaymentMethodID) REFERENCES PaymentMethod(PaymentMethodID)
);
GO

-- 12. ShoppingCart
CREATE TABLE ShoppingCart (
    CartID INT PRIMARY KEY IDENTITY(1,1),
    UserID INT NOT NULL UNIQUE,             -- Constraint 1:1 with user
    LastUpdated DATETIME NOT NULL DEFAULT GETDATE(),
    FOREIGN KEY (UserID) REFERENCES [User](UserID)
);
GO

-- 13. ShoppingCartItem (Weak Entity)
CREATE TABLE ShoppingCartItem (
    ItemID INT PRIMARY KEY IDENTITY (1, 1),
    CartID INT NOT NULL,
    ProductID INT NOT NULL,
    Quantity INT NOT NULL CHECK (Quantity > 0),
    AddedDate DATETIME NOT NULL DEFAULT GETDATE (),
    FOREIGN KEY (CartID) REFERENCES ShoppingCart (CartID),
    FOREIGN KEY (ProductID) REFERENCES Product (ProductID)
);
GO

-- 14. Review (Weak Entity, Corrected UNIQUE Constraint)
CREATE TABLE Review (
    ReviewID INT PRIMARY KEY IDENTITY(1,1),
    ProductID INT NOT NULL,
    BuyerID INT NOT NULL,                -- Buyer and his/her review
    Rating TINYINT NOT NULL CHECK (Rating BETWEEN 1 AND 5),
    Comment NVARCHAR(500),
    IsDeleted BIT NOT NULL DEFAULT 0,
    CreatedAt DATETIME NOT NULL DEFAULT GETDATE(),

-- Just only the buyers can rate this product

CONSTRAINT UQ_Review_BuyerProduct UNIQUE (ProductID, BuyerID),
    
    FOREIGN KEY (ProductID) REFERENCES Product(ProductID),
    FOREIGN KEY (BuyerID) REFERENCES [User](UserID)
);
GO

-- 15. ProductReviewLog (Weak Entity)
CREATE TABLE ProductReviewLog (
    LogID INT PRIMARY KEY IDENTITY(1,1),
    ProductID INT NOT NULL,
    ReviewerID INT NOT NULL,            -- Reviewer/Admin checked
    ActionType TINYINT NOT NULL,        -- 1: Approval, 2: Reject, 3: Edit
    Notes NVARCHAR(500),
    ActionDate DATETIME NOT NULL DEFAULT GETDATE(),
    FOREIGN KEY (ProductID) REFERENCES Product(ProductID),
    FOREIGN KEY (ReviewerID) REFERENCES [User](UserID)
);
GO

-- 16. SystemLog (Weak Entity)
CREATE TABLE SystemLog (
    LogID BIGINT PRIMARY KEY IDENTITY(1,1),
    UserID INT,                         -- Who performing operation (Admin/Reviewer)
    ActionType NVARCHAR(50) NOT NULL,   -- Ex: 'LOCK_USER', 'DELETE_PRODUCT', 'EXPORT_REPORT'
    TableName NVARCHAR(50),             -- The affected board
    RecordID INT,                       -- ID of affected record
    Description NVARCHAR(MAX),
    LogTime DATETIME NOT NULL DEFAULT GETDATE(),
    FOREIGN KEY (UserID) REFERENCES [User](UserID)
);
GO