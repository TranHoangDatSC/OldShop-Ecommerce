from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "OldShop E-Commerce API"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./sql_app.db"
    
    SECRET_KEY: str = "YOUR_SUPER_SECRET_KEY_HERE"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 giờ

    PAYPAL_CLIENT_ID: str = "ATo4XV367A3Jf1KG2BxskbucxSOyb_rIKqc9rNgxCDcwRhAYosZVhohADyFGUwkoAgCC3IhLpj2AAV0x"
    PAYPAL_SECRET: str = "EMe93wpK5-GjzDxZH0y7H_O14Wy9vjluFLJIlh6gPgT1uCzDCai2nxvLPRILDZjFiq40lCqIUegDdEeC"
    PAYPAL_MODE: str = "sandbox" # Hoặc "live"
    PAYPAL_API_URL: str = "https://api-m.sandbox.paypal.com"

    model_config = SettingsConfigDict(
        env_file=".env", 
        extra='ignore',
        str_min_length=1  # Đổi từ min_anystr_length thành str_min_length
    )

settings = Settings()