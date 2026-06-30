import pytest
from backend.services.sap_btp import SAPBTPService
from backend.core.config import Settings

@pytest.mark.asyncio
async def test_falls_back_to_mock_with_empty_credentials():
    settings = Settings(SAP_BTP_CLIENT_ID="", SAP_BTP_CLIENT_SECRET="", 
                         SAP_BTP_TOKEN_URL="", SAP_BTP_API_BASE_URL="")
    service = SAPBTPService(settings)
    result = await service.get_system_health()
    assert result is not None
    status = service.get_connection_status()
    assert status["mode"] == "mock"
    assert status["has_credentials"] == False

@pytest.mark.asyncio
async def test_falls_back_to_mock_with_placeholder_credentials():
    settings = Settings(
        SAP_BTP_CLIENT_ID="your_client_id",
        SAP_BTP_CLIENT_SECRET="your_secret",
        SAP_BTP_TOKEN_URL="https://placeholder.example.com",
        SAP_BTP_API_BASE_URL="https://placeholder.example.com"
    )
    service = SAPBTPService(settings)
    status = service.get_connection_status()
    assert status["has_credentials"] == False

@pytest.mark.asyncio
async def test_falls_back_to_mock_with_invalid_real_looking_credentials():
    """Credentials that look real but are wrong should fail gracefully, not crash."""
    settings = Settings(
        SAP_BTP_CLIENT_ID="sb-12345-fake",
        SAP_BTP_CLIENT_SECRET="fake-secret-value",
        SAP_BTP_TOKEN_URL="https://fake.authentication.sap.hana.ondemand.com",
        SAP_BTP_API_BASE_URL="https://fake.cfapps.sap.hana.ondemand.com"
    )
    service = SAPBTPService(settings)
    result = await service.get_system_health()
    assert result is not None  # must not crash, must return mock data
