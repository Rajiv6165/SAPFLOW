from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://sapflow:sapflow123@localhost:5432/sapflow"
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def coerce_database_url(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # SAP BTP Configuration
    SAP_BTP_HOST: Optional[str] = None
    SAP_CLIENT_ID: Optional[str] = None
    SAP_CLIENT_SECRET: Optional[str] = None
    SAP_TOKEN_URL: Optional[str] = None
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
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
