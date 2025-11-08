# init_manual.py
from app.core.database import SessionLocal, Base, engine
from app.models import sqlmodels
from app.initial_data import init_db
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.database import SessionLocal, Base, engine

def reset_and_init_db():
    print("👉 Bắt đầu reset và khởi tạo lại database...")
    # 1. Xóa toàn bộ bảng (nếu muốn reset hoàn toàn)
    Base.metadata.drop_all(bind=engine)
    # 2. Tạo lại tất cả bảng
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created.")

    # 3. Chạy khởi tạo dữ liệu mẫu
    db = SessionLocal()
    try:
        init_db(db)
        print("✅ Đã khởi tạo dữ liệu mẫu thành công.")
    except Exception as e:
        print(f"❌ Lỗi khi khởi tạo dữ liệu mẫu: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_and_init_db()