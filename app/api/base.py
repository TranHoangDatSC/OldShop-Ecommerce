from fastapi import APIRouter
from app.api.endpoints import auth, products, categories, users

api_router = APIRouter()

pi_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(categories.router, prefix="/categories", tags=["Categories"])
api_router.include_router(users.router, prefix="/users", tags=["users"])