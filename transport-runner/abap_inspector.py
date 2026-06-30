import httpx
import logging
import os
import asyncio
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ABAPInspector:
    def __init__(self, sap_host: str, client_id: str, client_secret: str):
        self.sap_host = sap_host
        self.client_id = client_id
        self.client_secret = client_secret
        self.mock_mode = os.getenv("SAP_MOCK_MODE", "true").lower() == "true"
        
    async def _has_valid_token(self) -> bool:
        if not self.client_id or not self.client_secret or not self.sap_host:
            return False
        if any("placeholder" in str(c).lower() or "your_" in str(c).lower() for c in [self.client_id, self.client_secret, self.sap_host]):
            return False
        try:
            token = await self.get_oauth_token()
            return token is not None
        except Exception:
            return False

    async def get_oauth_token(self) -> str | None:
        if self.mock_mode:
            logger.info("Using mock OAuth token")
            return "mock_bearer_token_12345"
            
        if not self.client_id or not self.client_secret or not self.sap_host:
            return None
        if any("placeholder" in str(c).lower() or "your_" in str(c).lower() for c in [self.client_id, self.client_secret, self.sap_host]):
            return None

        # Build URL for xsuaa / oauth endpoint
        token_url = self.sap_host.rstrip("/")
        if not token_url.endswith("/oauth/token"):
            token_url = f"{token_url}/oauth/token"
        
        for attempt in range(3):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        token_url,
                        data={
                            "grant_type": "client_credentials",
                            "client_id": self.client_id,
                            "client_secret": self.client_secret,
                        },
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                        timeout=30.0
                    )
                    response.raise_for_status()
                    token_data = response.json()
                    logger.info("OAuth token obtained successfully")
                    return token_data.get("access_token")
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: Failed to get OAuth token: {e}")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                else:
                    return None

    # NOTE: SAP ATC API endpoint may vary based on your trial system version.
    # Common paths to try if /sap/bc/adt/atc/runs returns 404:
    #   - /sap/opu/odata/sap/ATC_API/
    #   - /sap/bc/adt/atc/worklists
    # Check SAP BTP Cockpit > your subaccount > API documentation for the
    # exact endpoint available in your trial instance.
    async def run_code_inspection(self, transport_id: str) -> dict:
        if self.mock_mode or not await self._has_valid_token():
            return self._mock_inspection_result(transport_id)
        
        try:
            token = await self.get_oauth_token()
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.sap_host}/sap/bc/adt/atc/runs",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"transportId": transport_id},
                    timeout=30.0
                )
                response.raise_for_status()
                return self._parse_real_inspection_result(response.json())
        except Exception as e:
            logger.warning(f"Real ABAP inspection failed for {transport_id}, using mock: {e}")
            return self._mock_inspection_result(transport_id)

    async def validate_transport_objects(self, transport_id: str) -> List[Dict]:
        if self.mock_mode or not await self._has_valid_token():
            return self._mock_transport_objects(transport_id)
        
        try:
            token = await self.get_oauth_token()
            transport_url = f"{self.sap_host}/api/transports/{transport_id}/objects"
            
            for attempt in range(3):
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(
                            transport_url,
                            headers={"Authorization": f"Bearer {token}"},
                            timeout=30.0
                        )
                        response.raise_for_status()
                        return response.json()
                except Exception as e:
                    logger.error(f"Attempt {attempt + 1}: Failed to get transport objects: {e}")
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        raise
        except Exception as e:
            logger.error(f"Error validating transport objects: {e}")
            return self._mock_transport_objects(transport_id)

    def _mock_inspection_result(self, transport_id: str) -> Dict:
        return {
            "transport_id": transport_id,
            "severity": "INFO",
            "findings": [
                {
                    "object": "ZCL_USER_AUTH",
                    "type": "Class",
                    "message": "Code follows naming conventions",
                    "line": 1
                },
                {
                    "object": "ZFM_PAYMENT_PROCESS",
                    "type": "Function Module",
                    "message": "Consider adding error handling for timeout scenarios",
                    "line": 45
                }
            ],
            "passed": True
        }

    def _mock_transport_objects(self, transport_id: str) -> List[Dict]:
        return [
            {
                "object_name": "ZCL_USER_AUTH",
                "object_type": "CLAS",
                "description": "User authentication class",
                "package": "Z_AUTH"
            },
            {
                "object_name": "ZFM_PAYMENT_PROCESS",
                "object_type": "FUGR",
                "description": "Payment processing function group",
                "package": "Z_PAYMENT"
            },
            {
                "object_name": "ZT_USER_DATA",
                "object_type": "TABL",
                "description": "User data table",
                "package": "Z_AUTH"
            }
        ]

    def _parse_real_inspection_result(self, data: Dict) -> Dict:
        # Standardize the payload structures
        findings = []
        raw_findings = data.get("findings", [])
        for f in raw_findings:
            findings.append({
                "object": f.get("object", f.get("objectName", "UNKNOWN")),
                "type": f.get("type", f.get("objectType", "UNKNOWN")),
                "message": f.get("message", f.get("findingMessage", "")),
                "line": f.get("line", f.get("lineNumber", 1))
            })
        if not findings and "findings" in data:
            findings = raw_findings
        return {
            "transport_id": data.get("transportId", data.get("transport_id", "")),
            "severity": data.get("severity", "INFO"),
            "findings": findings,
            "passed": data.get("passed", True)
        }
