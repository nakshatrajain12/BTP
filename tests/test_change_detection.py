import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def dummy_schema():
    return {
        "scheme_name": "Test Grant",
        "ministry": "Ministry of Startups",
        "content_hash": "dummyhash123",
        "id": "123e4567-e89b-12d3-a456-426614174000"
    }

def test_hash_diff_logic(dummy_schema):
    # Simulate an old state vs new state change tracking
    old_version = {
        "content_hash": "oldhash999",
        "max_funding_amount": "500"
    }
    
    # Assert change detected condition
    assert old_version.get("content_hash") != dummy_schema.get("content_hash")
    
    # Check fields diff logic
    changed_fields = []
    for k, v in dummy_schema.items():
        if old_version.get(k) != v:
            changed_fields.append(k)
            
    assert "scheme_name" in changed_fields
    assert "content_hash" in changed_fields
