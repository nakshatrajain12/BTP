import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.schemas import SchemeRecord

def test_pydantic_validation_success():
    valid_data = {
        "scheme_name": "Test Grant",
        "ministry": "Ministry of Magic",
        "launch_year": 2025,
        "source_url": "http://example.gov.in",
        "funding_type": "grant",
        "max_funding_amount": "2000000",
        "sector_eligibility": ["deeptech", "ai"]
    }
    
    # Should not raise exception
    record = SchemeRecord(**valid_data)
    assert record.scheme_name == "Test Grant"
    assert record.max_funding_amount == 2000000
    
def test_pydantic_validation_failure():
    invalid_data = {
        # missing scheme_name
        "ministry": "Ministry of Magic",
        "source_url": "http://example.gov.in"
    }
    
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        SchemeRecord(**invalid_data)
