from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # SAP BTP Configuration
    SAP_BTP_HOST: str
    SAP_CLIENT_ID: str
    SAP_CLIENT_SECRET: str
    SAP_TOKEN_URL: str
    SAP_MOCK_MODE: bool = True
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "ap-south-1"
    AWS_ECR_REGISTRY: Optional[str] = None
    SNS_ALERT_TOPIC_ARN: Optional[str] = None
    
    # GitHub
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_REPO: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
