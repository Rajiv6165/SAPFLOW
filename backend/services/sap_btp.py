import httpx
import redis
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from backend.core.config import settings

logger = logging.getLogger(__name__)


class SAPBTPService:
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.access_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        
    async def get_oauth_token(self) -> str:
        if settings.SAP_MOCK_MODE:
            return "mock_bearer_token_12345"
        
        if self.access_token and self.token_expiry and datetime.utcnow() < self.token_expiry:
            return self.access_token
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.SAP_TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": settings.SAP_CLIENT_ID,
                    "client_secret": settings.SAP_CLIENT_SECRET,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in - 60)
            return self.access_token
    
    async def _get_cached_data(self, cache_key: str) -> Optional[Dict]:
        cached = self.redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        return None
    
    def _set_cached_data(self, cache_key: str, data: Dict, ttl: int = 30):
        self.redis_client.setex(cache_key, ttl, json.dumps(data))
    
    async def get_system_health(self) -> Dict:
        cache_key = "sap:system_health"
        cached = await self._get_cached_data(cache_key)
        if cached:
            return cached
        
        if settings.SAP_MOCK_MODE:
            data = {
                "cpu_percent": 45.2,
                "memory_percent": 62.8,
                "active_users": 127,
                "avg_response_ms": 245,
                "status": "healthy"
            }
        else:
            token = await self.get_oauth_token()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.SAP_BTP_HOST}/api/monitoring/health",
                    headers={"Authorization": f"Bearer {token}"}
                )
                response.raise_for_status()
                data = response.json()
        
        self._set_cached_data(cache_key, data, 30)
        return data
    
    async def get_active_transports(self) -> List[Dict]:
        cache_key = "sap:active_transports"
        cached = await self._get_cached_data(cache_key)
        if cached:
            return cached
        
        if settings.SAP_MOCK_MODE:
            data = [
                {
                    "transport_id": "DEVK900123",
                    "description": "Feature: User authentication enhancement",
                    "owner": "DEVELOPER01",
                    "status": "released",
                    "created_at": "2024-01-15T10:30:00Z"
                },
                {
                    "transport_id": "DEVK900124",
                    "description": "Bugfix: Payment gateway timeout",
                    "owner": "DEVELOPER02",
                    "status": "modifiable",
                    "created_at": "2024-01-16T14:20:00Z"
                }
            ]
        else:
            token = await self.get_oauth_token()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.SAP_BTP_HOST}/api/transports/active",
                    headers={"Authorization": f"Bearer {token}"}
                )
                response.raise_for_status()
                data = response.json()
        
        self._set_cached_data(cache_key, data, 30)
        return data
    
    async def get_transport_history(self, limit: int = 50) -> List[Dict]:
        cache_key = f"sap:transport_history:{limit}"
        cached = await self._get_cached_data(cache_key)
        if cached:
            return cached
        
        if settings.SAP_MOCK_MODE:
            data = [
                {
                    "transport_id": "DEVK900100",
                    "description": "Initial setup",
                    "source_system": "DEV",
                    "target_system": "QA",
                    "status": "success",
                    "completed_at": "2024-01-10T16:00:00Z"
                },
                {
                    "transport_id": "DEVK900099",
                    "description": "Database migration",
                    "source_system": "QA",
                    "target_system": "PROD",
                    "status": "success",
                    "completed_at": "2024-01-09T11:30:00Z"
                },
                {
                    "transport_id": "DEVK900098",
                    "description": "API endpoint update",
                    "source_system": "DEV",
                    "target_system": "QA",
                    "status": "failed",
                    "completed_at": "2024-01-08T09:15:00Z"
                }
            ]
        else:
            token = await self.get_oauth_token()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.SAP_BTP_HOST}/api/transports/history?limit={limit}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                response.raise_for_status()
                data = response.json()
        
        self._set_cached_data(cache_key, data, 30)
        return data
    
    async def promote_transport(self, transport_id: str, source: str, target: str) -> Dict:
        if settings.SAP_MOCK_MODE:
            return {
                "transport_id": transport_id,
                "source_system": source,
                "target_system": target,
                "status": "success",
                "message": f"Transport {transport_id} successfully promoted from {source} to {target}",
                "completed_at": datetime.utcnow().isoformat()
            }
        
        token = await self.get_oauth_token()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.SAP_BTP_HOST}/api/transports/promote",
                json={
                    "transport_id": transport_id,
                    "source_system": source,
                    "target_system": target
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            data = response.json()
        
        cache_key = "sap:active_transports"
        self.redis_client.delete(cache_key)
        return data
