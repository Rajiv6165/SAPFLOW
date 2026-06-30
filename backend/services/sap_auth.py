import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class SAPAuthClient:
    def __init__(self, client_id: str, client_secret: str, token_url: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self._cached_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
    
    async def get_token(self) -> Optional[str]:
        """
        Returns a valid bearer token, using cache if not expired.
        Returns None if credentials are missing/invalid (triggers mock mode).
        """
        # If client_id, client_secret, or token_url are empty or contain placeholder, return None immediately
        if not self.client_id or not self.client_secret or not self.token_url:
            return None
        
        for val in [self.client_id, self.client_secret, self.token_url]:
            if "placeholder" in val.lower() or "your_" in val.lower():
                return None
        
        # Check cache and refresh 60 seconds before actual expiry
        now = datetime.utcnow()
        if self._cached_token and self._token_expiry and now < (self._token_expiry - timedelta(seconds=60)):
            return self._cached_token
        
        # Formulate full URL: xsuaa expects POST to tokenurl/oauth/token with client_credentials
        # If the user has already included /oauth/token in token_url, don't duplicate it.
        url = self.token_url.rstrip("/")
        if not url.endswith("/oauth/token"):
            url = f"{url}/oauth/token"
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=15.0
                )
                response.raise_for_status()
                data = response.json()
                
                self._cached_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)
                self._token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
                
                logger.info("SAP BTP token refreshed successfully")
                return self._cached_token
        except Exception as e:
            logger.warning(f"SAP BTP OAuth2 flow failed, returning None (falling back to mock): {e}")
            return None
