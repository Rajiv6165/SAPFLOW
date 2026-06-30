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
    
    # SAP BTP Real Credentials (leave blank to use mock mode)
    SAP_BTP_CLIENT_ID: str = ""
    SAP_BTP_CLIENT_SECRET: str = ""
    SAP_BTP_TOKEN_URL: str = ""
    SAP_BTP_API_BASE_URL: str = ""

    @property
    def has_valid_sap_credentials(self) -> bool:
        """True only if all 4 SAP BTP credentials are present and don't look like placeholders."""
        creds = [self.SAP_BTP_CLIENT_ID, self.SAP_BTP_CLIENT_SECRET, 
                 self.SAP_BTP_TOKEN_URL, self.SAP_BTP_API_BASE_URL]
        if any(not c for c in creds):
            return False
        if any("placeholder" in c.lower() or "your_" in c.lower() for c in creds):
            return False
        return True
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "ap-south-1"
    AWS_ECR_REGISTRY: Optional[str] = None
    SNS_ALERT_TOPIC_ARN: Optional[str] = None
    
    # GitHub
    GITHUB_TOKEN: str = ""
    GITHUB_REPO: str = "Rajiv6165/sapflow"
    GITHUB_WEBHOOK_SECRET: str = "sapflow-webhook-secret-dev"
    PIPELINE_SYNC_INTERVAL: int = 60  # seconds between GitHub API syncs
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    # Production
    ENVIRONMENT: str = "development"  # development / production
    LOG_LEVEL: str = "INFO"
    ALLOWED_HOSTS: list[str] = ["*"]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def database_url_sync(self) -> str:
        # Return sync version of DATABASE_URL for Alembic
        return self.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
