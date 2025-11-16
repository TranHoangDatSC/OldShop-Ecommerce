from fastapi.responses import HTMLResponse
import uvicorn
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import engine, Base
from app.models import sqlmodels 
from app.initial_data import init_db
from app.core.database import SessionLocal 
from app.api.base import api_router
from fastapi import APIRouter
from app.api.endpoints import auth, products


# --- 🛠️ HÀM TẠO BẢNG DATABASE (ĐƯỢC KÍCH HOẠT LẠI) ---
def create_tables():
    """Tạo tất cả các bảng dựa trên Base.metadata."""
    # Đảm bảo các models đã được import (như dòng 6) trước khi gọi Base.metadata.create_all
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully or already exist.")

# --- 🛠️ HÀM KHỞI TẠO DỮ LIỆU BAN ĐẦU (ĐƯỢC KÍCH HOẠT LẠI) ---
def initialize_database():
    """Tạo bảng và chèn dữ liệu khởi tạo."""
    create_tables() 
    try:
        db = SessionLocal()
        init_db(db)
        print("Initial data inserted successfully.")
    except Exception as e:
        # Lỗi này thường xảy ra nếu init_db được chạy nhiều lần.
        print(f"Lỗi khi khởi tạo DB/Dữ liệu ban đầu (có thể do dữ liệu đã tồn tại): {e}")
    finally:
        if 'db' in locals() and db:
            db.close() 

# Khởi tạo Database ngay khi module main.py được loade
# initialize_database()

# --- KHỞI TẠO APP FASTAPI ---
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Cấu hình Static và Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.mount("/templates", StaticFiles(directory="app/templates"), name="templates")
@app.get("/")
def read_root(request: Request):
    """Render trang index.html."""
    return templates.TemplateResponse("index.html", {"request": request})
app.mount("/templates", StaticFiles(directory="app/templates"), name="templates")

@app.get("/")
def read_root(request: Request):
    """Render trang cart.html."""
    return templates.TemplateResponse("cart.html", {"request": request})

@app.get("/")
def read_root(request: Request):
    """Render trang shop.html."""
    return templates.TemplateResponse("shop.html", {"request": request})

# Router Dashboard Người dùng Quản lý:
@app.get("/user/seller_dashboard.html", response_class=HTMLResponse)
async def seller_dashboard_page(request: Request):
    return templates.TemplateResponse("user/seller_dashboard.html", {"request": request})

# Router Dashboard Moderator:
@app.get("/moderator/moderator_dashboard.html", response_class=HTMLResponse)
async def moderator_dashboard(request: Request):
    """Phục vụ tệp HTML cho trang kiểm duyệt viên."""
    return templates.TemplateResponse("moderator/moderator_dashboard.html", {"request": request})

@app.get("/moderator/moderator_products.html", response_class=HTMLResponse)
async def moderator_product_page(request: Request):
    return templates.TemplateResponse("moderator/moderator_products.html", {"request": request})
@app.get("/moderator/moderator_users.html", response_class=HTMLResponse)
async def moderator_users_page(request: Request):
    return templates.TemplateResponse("moderator/moderator_users.html", {"request": request})


# Router Dashboard Admin:
@app.get("/admin/dashboard_admin.html", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Phục vụ tệp HTML cho trang quản trị."""
    return templates.TemplateResponse("admin/dashboard_admin.html", {"request": request})

# Router Admin Quản lý các tài khoản:
@app.get("/admin/admin_moderators.html", response_class=HTMLResponse)
async def admin_moderators_page(request: Request):
    return templates.TemplateResponse("admin/admin_moderators.html", {"request": request})
@app.get("/admin/admin_users.html", response_class=HTMLResponse)
async def admin_users_page(request: Request): # Đổi tên hàm để tránh trùng lặp
    return templates.TemplateResponse("admin/admin_users.html", {"request": request})

# ROUTE CHÍNH
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(products.router, prefix="/api/products")


if __name__ == "__main__":
    # Đảm bảo uvicorn chạy đúng file app
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)