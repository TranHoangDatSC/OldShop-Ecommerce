from enum import IntEnum

# --- HẰNG SỐ CỦA ROLE (Vai trò) ---

class RoleID(IntEnum):
    """Định nghĩa ID của các vai trò trong hệ thống."""
    ADMIN = 1
    MODERATOR = 2
    CUSTOMER = 3 # Khách hàng (cũng là người bán/User mặc định)

# 🔥 KHẮC PHỤC LỖI IMPORT: Định nghĩa hằng số mặc định dựa trên Enum 🔥
DEFAULT_USER_ROLE_ID = RoleID.CUSTOMER.value # Giá trị là 3

# --- HẰNG SỐ CỦA PRODUCT STATUS (Trạng thái Sản phẩm) ---

class ProductStatus(IntEnum):
    """Định nghĩa trạng thái của một sản phẩm."""
    PENDING = 0      # Đang chờ duyệt (Mặc định khi tạo)
    APPROVED = 1     # Đã được duyệt và đang bán
    REJECTED = 2     # Bị từ chối

# --- HẰNG SỐ CỦA ORDER STATUS (Trạng thái Đơn hàng) ---

class OrderStatus(IntEnum):
    """Định nghĩa trạng thái của một đơn hàng."""
    PENDING = 0
    PROCESSING = 1
    SHIPPED = 2
    DELIVERED = 3
    CANCELED = 4

# --- HẰNG SỐ CỦA PAYMENT METHOD (Phương thức Thanh toán) ---
# Dùng để tham chiếu đến PaymentMethodID trong bảng Order.
# Tên và ID sẽ phụ thuộc vào dữ liệu khởi tạo (seed data)
class PaymentMethodID(IntEnum):
    CASH_ON_DELIVERY = 1 # COD (Thanh toán khi nhận hàng)
    CREDIT_CARD = 2      # Thẻ tín dụng
    BANK_TRANSFER = 3    # Chuyển khoản ngân hàng 
    
# --- CÁC HẰNG SỐ KHÁC (Tùy chọn) ---
# Ví dụ: Độ dài tối thiểu của mật khẩu/tên người dùng
MIN_PASSWORD_LENGTH = 6
MIN_USERNAME_LENGTH = 3