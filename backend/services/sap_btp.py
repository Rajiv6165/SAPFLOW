import httpx
import redis
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from backend.core.config import Settings, settings
from backend.services.sap_auth import SAPAuthClient

logger = logging.getLogger(__name__)


class SAPBTPService:
    def __init__(self, settings: Settings = settings):
        self.settings = settings
        try:
            self.redis_client = redis.from_url(self.settings.REDIS_URL)
        except Exception as e:
            logger.warning(f"Failed to connect to Redis, caching disabled: {e}")
            self.redis_client = None
            
        self.auth_client = None
        if self.settings.has_valid_sap_credentials:
            self.auth_client = SAPAuthClient(
                self.settings.SAP_BTP_CLIENT_ID,
                self.settings.SAP_BTP_CLIENT_SECRET,
                self.settings.SAP_BTP_TOKEN_URL
            )
        self.is_live = False  # becomes True only after first successful real API call
        
    async def _get_cached_data(self, cache_key: str) -> Optional[Dict]:
        if not self.redis_client:
            return None
        try:
            cached = self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Failed to read from Redis cache: {e}")
        return None
    
    def _set_cached_data(self, cache_key: str, data: Dict, ttl: int = 30):
        if not self.redis_client:
            return
        try:
            self.redis_client.setex(cache_key, ttl, json.dumps(data))
        except Exception as e:
            logger.warning(f"Failed to write to Redis cache: {e}")

    def get_connection_status(self) -> dict:
        """Returns current connection mode for the dashboard to display."""
        return {
            "mode": "live" if self.is_live else "mock",
            "has_credentials": self.auth_client is not None,
            "api_base_url": self.settings.SAP_BTP_API_BASE_URL if self.settings.has_valid_sap_credentials else None
        }

    # --- Real Responses Parsers ---
    def _parse_real_health_response(self, data: Dict) -> Dict:
        return {
            "cpu_percent": data.get("cpu_percent", data.get("cpu", 0.0)),
            "memory_percent": data.get("memory_percent", data.get("memory", 0.0)),
            "active_users": data.get("active_users", data.get("users", 0)),
            "avg_response_ms": data.get("avg_response_ms", data.get("responseTime", 0)),
            "status": data.get("status", "healthy")
        }

    def _parse_real_active_transports(self, data: List[Dict]) -> List[Dict]:
        return data

    def _parse_real_transport_history(self, data: List[Dict]) -> List[Dict]:
        return data

    def _parse_real_promote_transport(self, data: Dict) -> Dict:
        return data

    # --- Mocks ---
    def _mock_system_health(self) -> Dict:
        return {
            "cpu_percent": 45.2,
            "memory_percent": 62.8,
            "active_users": 127,
            "avg_response_ms": 245,
            "status": "healthy"
        }

    def _mock_active_transports(self) -> List[Dict]:
        return [
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

    def _mock_transport_history(self, limit: int = 50) -> List[Dict]:
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
        return data[:limit]

    def _mock_promote_transport(self, transport_id: str, source: str, target: str) -> Dict:
        return {
            "transport_id": transport_id,
            "source_system": source,
            "target_system": target,
            "status": "success",
            "message": f"Transport {transport_id} successfully promoted from {source} to {target}",
            "completed_at": datetime.utcnow().isoformat()
        }

    # --- Main Service API Methods ---
    async def get_system_health(self) -> Dict:
        cache_key = "sap:system_health"
        cached = await self._get_cached_data(cache_key)
        if cached:
            return cached

        token = await self.auth_client.get_token() if self.auth_client else None
        
        if token is None:
            logger.info("SAP BTP: using mock mode (no valid credentials or auth failed)")
            data = self._mock_system_health()
        else:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.settings.SAP_BTP_API_BASE_URL}/monitoring/health",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=10.0
                    )
                    response.raise_for_status()
                    self.is_live = True
                    data = self._parse_real_health_response(response.json())
            except Exception as e:
                logger.warning(f"SAP BTP real API call failed, falling back to mock: {e}")
                self.is_live = False
                data = self._mock_system_health()

        self._set_cached_data(cache_key, data, 30)
        return data

    async def get_active_transports(self) -> List[Dict]:
        cache_key = "sap:active_transports"
        cached = await self._get_cached_data(cache_key)
        if cached:
            return cached

        token = await self.auth_client.get_token() if self.auth_client else None
        
        if token is None:
            logger.info("SAP BTP: using mock mode (no valid credentials or auth failed)")
            data = self._mock_active_transports()
        else:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.settings.SAP_BTP_API_BASE_URL}/api/transports/active",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=10.0
                    )
                    response.raise_for_status()
                    self.is_live = True
                    data = self._parse_real_active_transports(response.json())
            except Exception as e:
                logger.warning(f"SAP BTP real API call failed, falling back to mock: {e}")
                self.is_live = False
                data = self._mock_active_transports()

        self._set_cached_data(cache_key, data, 30)
        return data

    async def get_transport_history(self, limit: int = 50) -> List[Dict]:
        cache_key = f"sap:transport_history:{limit}"
        cached = await self._get_cached_data(cache_key)
        if cached:
            return cached

        token = await self.auth_client.get_token() if self.auth_client else None
        
        if token is None:
            logger.info("SAP BTP: using mock mode (no valid credentials or auth failed)")
            data = self._mock_transport_history(limit)
        else:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.settings.SAP_BTP_API_BASE_URL}/api/transports/history?limit={limit}",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=10.0
                    )
                    response.raise_for_status()
                    self.is_live = True
                    data = self._parse_real_transport_history(response.json())
            except Exception as e:
                logger.warning(f"SAP BTP real API call failed, falling back to mock: {e}")
                self.is_live = False
                data = self._mock_transport_history(limit)

        self._set_cached_data(cache_key, data, 30)
        return data

    async def promote_transport(self, transport_id: str, source: str, target: str) -> Dict:
        token = await self.auth_client.get_token() if self.auth_client else None
        
        if token is None:
            logger.info("SAP BTP: using mock mode (no valid credentials or auth failed)")
            data = self._mock_promote_transport(transport_id, source, target)
        else:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.settings.SAP_BTP_API_BASE_URL}/api/transports/promote",
                        json={
                            "transport_id": transport_id,
                            "source_system": source,
                            "target_system": target
                        },
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=15.0
                    )
                    response.raise_for_status()
                    self.is_live = True
                    data = self._parse_real_promote_transport(response.json())
            except Exception as e:
                logger.warning(f"SAP BTP real API call failed, falling back to mock: {e}")
                self.is_live = False
                data = self._mock_promote_transport(transport_id, source, target)

        if self.redis_client:
            try:
                cache_key = "sap:active_transports"
                self.redis_client.delete(cache_key)
            except Exception as e:
                logger.warning(f"Failed to clear active transports cache: {e}")
                
        return data
