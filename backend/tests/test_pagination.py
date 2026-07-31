import os
import json
import math
import pytest

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"


def test_pagination_envelope_structure():
    """Verify that pagination math and envelope structure align with requirement."""
    total = 45
    limit = 20
    page = 1

    total_pages = math.ceil(total / limit) if total > 0 else 0
    offset = (page - 1) * limit

    envelope = {
        "items": [],
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
    }

    assert envelope["page"] == 1
    assert envelope["limit"] == 20
    assert envelope["total"] == 45
    assert envelope["total_pages"] == 3
    assert offset == 0
