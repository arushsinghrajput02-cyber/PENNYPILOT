import os
from typing import List
from dotenv import load_dotenv

# Load local environment variables from .env
load_dotenv()


class Settings:
    PROJECT_NAME: str = "PennyPilot"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "pennypilot-super-secure-dev-secret-key-college-btech-cse-2026")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./pennypilot.db")
    
    # CORS configuration
    CORS_ORIGINS_RAW: str = os.getenv(
        "CORS_ORIGINS", 
        "http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000,http://127.0.0.1:3000,http://localhost:5500,http://127.0.0.1:5500"
    )
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS_RAW.split(",") if origin.strip()]


settings = Settings()
