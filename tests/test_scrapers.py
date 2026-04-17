import pytest
import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.base_scraper import compute_hash

def test_base_scraper_hashing():
    content = {"title": "Mock Scheme", "body": "some text"}
    hash_val = compute_hash(content)
    
    # Verify hash determinism
    assert len(hash_val) == 64
    assert hash_val == compute_hash(content)
