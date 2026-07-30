import pytest
from pydantic import ValidationError
from backend.models.schemas import TransportPromoteRequest


# ─── Pytest Fixtures for Reusable Sample Payloads ─────────────────────────────

@pytest.fixture
def valid_transport_payload():
    """Fixture providing a valid baseline transport promotion request payload."""
    return {
        "transport_id": "DEVK900123",
        "source_system": "DEV",
        "target_system": "QA",
        "promoted_by": "developer1",
        "landscape": "DEFAULT"
    }


@pytest.fixture
def prod_promotion_payload():
    """Fixture providing a valid promotion payload targeting PROD."""
    return {
        "transport_id": "QASK900456",
        "source_system": "QA",
        "target_system": "PROD",
        "promoted_by": "release_manager",
        "landscape": "FINANCE"
    }


@pytest.fixture
def dev_target_payload():
    """Fixture providing a payload incorrectly targeting DEV as promotion destination."""
    return {
        "transport_id": "QASK900456",
        "source_system": "QA",
        "target_system": "DEV",
        "promoted_by": "user1"
    }


# ─── 1. Valid Transport ID Formats ───────────────────────────────────────────

@pytest.mark.parametrize("transport_id", [
    "DEVK900123",
    "QASK900456",
    "PRDK123456",
    "SYSK999999",
    "FINK000001",
    "LOGK111111",
])
def test_valid_transport_id_formats(valid_transport_payload, transport_id):
    """Test that valid SAP transport ID formats pass validation successfully."""
    payload = valid_transport_payload.copy()
    payload["transport_id"] = transport_id
    
    request = TransportPromoteRequest(**payload)
    assert request.transport_id == transport_id
    assert request.source_system == "DEV"
    assert request.target_system == "QA"


def test_valid_promote_request_fixture(valid_transport_payload):
    """Test creating a TransportPromoteRequest using the baseline fixture."""
    request = TransportPromoteRequest(**valid_transport_payload)
    assert request.transport_id == "DEVK900123"
    assert request.promoted_by == "developer1"
    assert request.landscape == "DEFAULT"


def test_valid_promote_to_prod_fixture(prod_promotion_payload):
    """Test valid promotion request to PROD system using fixture."""
    request = TransportPromoteRequest(**prod_promotion_payload)
    assert request.transport_id == "QASK900456"
    assert request.source_system == "QA"
    assert request.target_system == "PROD"


# ─── 2. Invalid Transport ID Formats ─────────────────────────────────────────

def test_invalid_transport_id_empty(valid_transport_payload):
    """Test that an empty string transport_id raises a ValidationError."""
    payload = valid_transport_payload.copy()
    payload["transport_id"] = ""
    
    with pytest.raises(ValidationError) as exc_info:
        TransportPromoteRequest(**payload)
    assert "transport_id cannot be empty" in str(exc_info.value)


def test_invalid_transport_id_whitespace(valid_transport_payload):
    """Test that a whitespace-only transport_id raises a ValidationError."""
    payload = valid_transport_payload.copy()
    payload["transport_id"] = "   "
    
    with pytest.raises(ValidationError) as exc_info:
        TransportPromoteRequest(**payload)
    assert "transport_id cannot be empty" in str(exc_info.value)


@pytest.mark.parametrize("invalid_id", [
    "INVALID",          # Arbitrary text
    "devk900123",       # Lowercase
    "DEV1234567",       # Missing 'K' separator
    "DEVK90012",        # Too short (5 digits instead of 6)
    "DEVK9001234",      # Too long (7 digits instead of 6)
    "DEVK90012A",       # Non-digit suffix
    "DK900123",         # 2-letter system ID prefix
    "DEVK1900123",      # Extra character in middle
    "1234567890",       # Numeric only
    "DEVK-900123",      # Hyphenated
])
def test_invalid_transport_id_patterns(valid_transport_payload, invalid_id):
    """Test that non-matching transport ID patterns raise format validation errors."""
    payload = valid_transport_payload.copy()
    payload["transport_id"] = invalid_id
    
    with pytest.raises(ValidationError) as exc_info:
        TransportPromoteRequest(**payload)
    assert "transport_id must match SAP format" in str(exc_info.value)


# ─── 3. Invalid Target System / Landscape Values ──────────────────────────────

@pytest.mark.parametrize("invalid_target", [
    "INVALID",
    "STAGE",
    "TEST",
    "123",
    "PRODUCTION",
    "QUALITY",
    "dev",
    "qa",
])
def test_invalid_target_system_values(valid_transport_payload, invalid_target):
    """Test that target_system values outside of DEV/QA/PROD raise validation errors."""
    payload = valid_transport_payload.copy()
    payload["target_system"] = invalid_target
    
    with pytest.raises(ValidationError) as exc_info:
        TransportPromoteRequest(**payload)
    assert "target_system must be one of" in str(exc_info.value)


# ─── 4. Rejection of DEV as a Promotion Target ────────────────────────────────

def test_rejection_of_dev_target_fixture(dev_target_payload):
    """Test that attempting to promote to DEV using dev_target_payload fixture is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        TransportPromoteRequest(**dev_target_payload)
    assert "Cannot promote to DEV" in str(exc_info.value)


@pytest.mark.parametrize("source", ["DEV", "QA", "PROD"])
def test_rejection_of_dev_target_from_any_source(valid_transport_payload, source):
    """Test that DEV is strictly rejected as a promotion target regardless of source system."""
    payload = valid_transport_payload.copy()
    payload["source_system"] = source
    payload["target_system"] = "DEV"
    
    with pytest.raises(ValidationError) as exc_info:
        TransportPromoteRequest(**payload)
    assert "Cannot promote to DEV (backwards promotion not allowed)" in str(exc_info.value)
