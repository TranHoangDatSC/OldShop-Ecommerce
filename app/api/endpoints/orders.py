from app.core.config import settings
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models import schemas
from app.crud.crud_order import order_crud
from app.crud.crud_cart import cart_crud
from app.core.database import get_db
import requests
from requests.auth import HTTPBasicAuth

router = APIRouter()

@router.post("/", response_model=schemas.Order)
def create_order(
    *,
    db: Session = Depends(get_db),
    obj_in: schemas.OrderCreate, # Schema này yêu cầu ContactInfo ở Body
    current_user = Depends(deps.get_current_user)
):
    try:
        # Gọi hàm tạo đơn
        order = order_crud.create_simple_order(
            db, 
            user_id=current_user.UserID, 
            payment_method_id=obj_in.PaymentMethodID,
            items_in=obj_in.items
        )
        # Xóa giỏ hàng
        cart_crud.clear_cart(db, user_id=current_user.UserID)
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback() # Trả lại trạng thái cũ nếu crash
        print(f"CRITICAL CHECKOUT ERROR: {e}")
        raise HTTPException(status_code=500, detail="Thanh toán thất bại.")
    
# 1. Hàm bổ trợ lấy Access Token từ PayPal (Thay cho Client SDK của .NET)
def get_paypal_access_token():
    try:
        # Đảm bảo dùng đúng đường dẫn từ app.core.config
        from app.core.config import settings
        
        auth = HTTPBasicAuth(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET)
        print(f"DEBUG: Using ClientID: {settings.PAYPAL_CLIENT_ID[:10]}...") # Chỉ in 10 ký tự đầu để bảo mật

        response = requests.post(
            f"{settings.PAYPAL_API_URL}/v1/oauth2/token",
            auth=auth,
            data={"grant_type": "client_credentials"},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"PAYPAL AUTH ERROR: {response.status_code} - {response.text}")
            return None
            
        return response.json().get("access_token")
    except Exception as e:
        print(f"PAYPAL EXCEPTION: {str(e)}")
        return None

# 2. Endpoint tạo Order trên PayPal
@router.post("/create-paypal-order")
async def create_paypal_order(
    db: Session = Depends(get_db),
    current_user = Depends(deps.get_current_user)
):
    token = get_paypal_access_token()
    if not token:
        raise HTTPException(status_code=500, detail="Không thể xác thực với PayPal (Check ClientID/Secret)")
    
    cart = cart_crud.get_user_cart(db, user_id=current_user.UserID)
    # Tính tổng tiền (VND -> USD vì PayPal Sandbox VN kén VND)
    total_vnd = sum(item.product.Price * item.Quantity for item in cart.items) + 10000
    total_usd = str(round(total_vnd / 25000, 2)) 

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {"currency_code": "USD", "value": total_usd}
        }]
    }
    
    res = requests.post(f"{settings.PAYPAL_API_URL}/v2/checkout/orders", json=payload, headers=headers)
    
    if res.status_code != 201:
        print(f"PAYPAL ORDER CREATE ERROR: {res.text}")
        raise HTTPException(status_code=400, detail="PayPal từ chối tạo đơn hàng")
        
    return res.json()

# 3. Endpoint Capture (Sau khi khách Approve trên giao diện)
@router.post("/capture-paypal-order/{paypal_order_id}")
async def capture_paypal_order(
    paypal_order_id: str,
    obj_in: schemas.OrderCreate, # Để lấy thông tin items
    db: Session = Depends(get_db),
    current_user = Depends(deps.get_current_user)
):
    token = get_paypal_access_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Capture tiền
    res = requests.post(f"{settings.PAYPAL_API_URL}/v2/checkout/orders/{paypal_order_id}/capture", headers=headers)
    
    if res.status_code in [200, 201]:
        # Tương đương đoạn lưu HoaDon/ChiTietHd trong C# của bạn
        order = order_crud.create_simple_order(
            db, user_id=current_user.UserID, 
            payment_method_id=2, # Giả sử 2 là PayPal
            items_in=obj_in.items
        )
        cart_crud.clear_cart(db, user_id=current_user.UserID)
        return {"status": "success", "order_id": order.OrderID}
    
    raise HTTPException(status_code=400, detail="Thanh toán PayPal không thành công.")