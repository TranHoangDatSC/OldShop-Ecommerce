import os
import secrets # Dùng secrets.token_hex thay vì os.urandom.hex() để đơn giản và an toàn hơn
from datetime import datetime, timedelta
from typing import Optional, Any
from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings # Giả định import settings thành công
import secrets

def generate_random_key(length: int = 32) -> str:
    """Sinh khóa API ngẫu nhiên (hexadecimal)"""
    return secrets.token_hex(length)

# Sử dụng bcrypt để hash mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- 1. Xử lý Mật khẩu ---

# 🔥 Sửa tên hàm để khớp với import: generate_random_key -> create_random_key
def create_random_key(length: int = 32) -> str:
    """Tạo một chuỗi ngẫu nhiên an toàn (sử dụng làm salt/random key)."""
    # Sử dụng secrets.token_hex() an toàn hơn os.urandom().hex()
    return secrets.token_hex(length // 2)[:length] 

# 🔥 Cải thiện bảo mật: Sử dụng bcrypt thay vì SHA-256
def get_password_hash(password: str, salt: str) -> str:
    """
    Tạo hash mật khẩu an toàn bằng bcrypt.
    Lưu ý: Bcrypt đã có salt riêng. Chúng ta kết hợp salt (RandomKey)
    với mật khẩu gốc để thêm một lớp bảo mật nếu cần.
    """
    # Nối salt (RandomKey) vào mật khẩu trước khi hash
    salted_password = password + salt 
    return pwd_context.hash(salted_password)

# 🔥 Cải thiện bảo mật: Sử dụng bcrypt để verify
def verify_password(plain_password: str, hashed_password: str, salt: str) -> bool:
    """Kiểm tra mật khẩu thường và mật khẩu đã hash bằng bcrypt."""
    salted_password = plain_password + salt
    try:
        return pwd_context.verify(salted_password, hashed_password)
    except ValueError:
        # Xảy ra nếu hashed_password không phải là định dạng bcrypt hợp lệ (ví dụ: hash cũ)
        return False

# --- 2. Xử lý JWT Token (Không thay đổi, logic đã ổn) ---

def create_access_token(
    subject: str | Any, 
    expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.JWTError:
        return None