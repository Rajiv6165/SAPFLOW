import os
import json
import pytest

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from fastapi import Request
from slowapi.errors import RateLimitExceeded
from backend.main import _rate_limit_exceeded_handler


class MockLimit:
    error_message = None
    limit = "10 per 1 minute"


def test_rate_limit_exceeded_handler():
    """Test that RateLimitExceeded handler returns 429 with 'Rate limit exceeded' message."""
    dummy_request = Request({"type": "http", "method": "GET", "path": "/test", "headers": []})
    exc = RateLimitExceeded(MockLimit())

    response = _rate_limit_exceeded_handler(dummy_request, exc)

    assert response.status_code == 429
    data = json.loads(response.body.decode())
    assert "Rate limit exceeded" in data["detail"]
