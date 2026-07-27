import pytest
from backend.models.schemas import TransportPromoteRequest
from pydantic import ValidationError


def test_valid_transport_promote_request():
    """Test valid transport promotion request."""
    request = TransportPromoteRequest(
        transport_id="DEVK900123",
        source_system="DEV",
        target_system="QA",
        promoted_by="user1"
    )
    assert request.transport_id == "DEVK900123"
    assert request.source_system == "DEV"
    assert request.target_system == "QA"


def test_invalid_transport_id_empty():
    """Test that empty transport_id raises validation error."""
    with pytest.raises(ValidationError) as exc_info:
        TransportPromoteRequest(
            transport_id="",
            source_system="DEV",
            target_system="QA"
        )
    assert "transport_id cannot be empty" in str(exc_info.value)


def test_invalid_transport_id_format():
    """Test that invalid transport ID format raises validation error."""
    with pytest.raises(ValidationError) as exc_info:
        TransportPromoteRequest(
            transport_id="INVALID",
            source_system="DEV",
            target_system="QA"
        )
    assert "transport_id must match SAP format" in str(exc_info.value)


def test_invalid_target_system():
    """Test that invalid target_system raises validation error."""
    with pytest.raises(ValidationError) as exc_info:
        TransportPromoteRequest(
            transport_id="DEVK900123",
            source_system="DEV",
            target_system="INVALID"
        )
    assert "target_system must be one of" in str(exc_info.value)


def test_backwards_promotion_to_dev():
    """Test that promotion to DEV (backwards) raises validation error."""
    with pytest.raises(ValidationError) as exc_info:
        TransportPromoteRequest(
            transport_id="DEVK900123",
            source_system="QA",
            target_system="DEV"
        )
    assert "Cannot promote to DEV" in str(exc_info.value)


def test_valid_promote_to_prod():
    """Test valid promotion to PROD."""
    request = TransportPromoteRequest(
        transport_id="QAK900456",
        source_system="QA",
        target_system="PROD"
    )
    assert request.target_system == "PROD"


def test_transport_id_whitespace():
    """Test that whitespace-only transport_id raises validation error."""
    with pytest.raises(ValidationError) as exc_info:
        TransportPromoteRequest(
            transport_id="   ",
            source_system="DEV",
            target_system="QA"
        )
    assert "transport_id cannot be empty" in str(exc_info.value)
