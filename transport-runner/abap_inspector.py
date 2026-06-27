import requests
import logging
import os
from typing import Dict, List
from time import sleep

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ABAPInspector:
    def __init__(self, sap_host: str, client_id: str, client_secret: str):
        self.sap_host = sap_host
        self.client_id = client_id
        self.client_secret = client_secret
        self.mock_mode = os.getenv("SAP_MOCK_MODE", "true").lower() == "true"
        
    def get_oauth_token(self) -> str:
        if self.mock_mode:
            logger.info("Using mock OAuth token")
            return "mock_bearer_token_12345"
        
        token_url = f"{self.sap_host}/oauth/token"
        
        for attempt in range(3):
            try:
                response = requests.post(
                    token_url,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=30
                )
                response.raise_for_status()
                token_data = response.json()
                logger.info("OAuth token obtained successfully")
                return token_data["access_token"]
            except requests.exceptions.RequestException as e:
                logger.error(f"Attempt {attempt + 1}: Failed to get OAuth token: {e}")
                if attempt < 2:
                    sleep(2 ** attempt)
                else:
                    raise
    
    def run_code_inspection(self, transport_id: str) -> Dict:
        if self.mock_mode:
            logger.info(f"Running mock code inspection for transport {transport_id}")
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
        
        try:
            token = self.get_oauth_token()
            inspection_url = f"{self.sap_host}/api/code-inspector"
            
            for attempt in range(3):
                try:
                    response = requests.post(
                        inspection_url,
                        json={"transport_id": transport_id},
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=60
                    )
                    response.raise_for_status()
                    result = response.json()
                    logger.info(f"Code inspection completed for transport {transport_id}")
                    return result
                except requests.exceptions.RequestException as e:
                    logger.error(f"Attempt {attempt + 1}: Code inspection failed: {e}")
                    if attempt < 2:
                        sleep(2 ** attempt)
                    else:
                        raise
        except Exception as e:
            logger.error(f"Error running code inspection: {e}")
            raise
    
    def validate_transport_objects(self, transport_id: str) -> List[Dict]:
        if self.mock_mode:
            logger.info(f"Running mock transport object validation for {transport_id}")
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
        
        try:
            token = self.get_oauth_token()
            transport_url = f"{self.sap_host}/api/transports/{transport_id}/objects"
            
            for attempt in range(3):
                try:
                    response = requests.get(
                        transport_url,
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=30
                    )
                    response.raise_for_status()
                    objects = response.json()
                    logger.info(f"Transport objects retrieved for {transport_id}")
                    return objects
                except requests.exceptions.RequestException as e:
                    logger.error(f"Attempt {attempt + 1}: Failed to get transport objects: {e}")
                    if attempt < 2:
                        sleep(2 ** attempt)
                    else:
                        raise
        except Exception as e:
            logger.error(f"Error validating transport objects: {e}")
            raise
