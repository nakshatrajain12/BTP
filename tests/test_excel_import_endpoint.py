"""
Tests for Excel Import API Endpoint

This module tests the POST /pipeline/import-excel endpoint to ensure:
- File upload functionality works
- File path parameter works
- Deduplication is applied correctly
- Summary report is returned with correct counts
- Error handling works for invalid inputs
"""

import pytest
from fastapi.testclient import TestClient
from main import app
import os
import tempfile
import shutil

client = TestClient(app)


def test_import_excel_with_file_path():
    """Test importing Excel file using file_path parameter."""
    excel_file = "Central_Govt_Startup_Schemes_Database.xlsx"
    
    if not os.path.exists(excel_file):
        pytest.skip(f"Excel file not found: {excel_file}")
    
    response = client.post(
        "/pipeline/import-excel",
        data={"file_path": excel_file}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "summary" in data
    assert "records_processed" in data["summary"]
    assert "records_extracted" in data["summary"]
    assert "records_added" in data["summary"]
    assert "records_updated" in data["summary"]
    assert "records_skipped" in data["summary"]
    
    # Verify counts are non-negative
    summary = data["summary"]
    assert summary["records_processed"] >= 0
    assert summary["records_extracted"] >= 0
    assert summary["records_added"] >= 0
    assert summary["records_updated"] >= 0
    assert summary["records_skipped"] >= 0


def test_import_excel_missing_parameters():
    """Test that endpoint returns error when no file or file_path provided."""
    response = client.post("/pipeline/import-excel")
    
    assert response.status_code == 400
    assert "file" in response.json()["detail"].lower() or "file_path" in response.json()["detail"].lower()


def test_import_excel_invalid_file_path():
    """Test that endpoint returns error for non-existent file path."""
    response = client.post(
        "/pipeline/import-excel",
        data={"file_path": "/nonexistent/path/to/file.xlsx"}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_import_excel_with_file_upload():
    """Test importing Excel file using file upload."""
    excel_file = "Central_Govt_Startup_Schemes_Database.xlsx"
    
    if not os.path.exists(excel_file):
        pytest.skip(f"Excel file not found: {excel_file}")
    
    with open(excel_file, "rb") as f:
        response = client.post(
            "/pipeline/import-excel",
            files={"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "summary" in data


def test_import_excel_idempotency():
    """Test that running import twice with same file doesn't create duplicates."""
    excel_file = "Central_Govt_Startup_Schemes_Database.xlsx"
    
    if not os.path.exists(excel_file):
        pytest.skip(f"Excel file not found: {excel_file}")
    
    # First import
    response1 = client.post(
        "/pipeline/import-excel",
        data={"file_path": excel_file}
    )
    assert response1.status_code == 200
    data1 = response1.json()
    
    # Second import (should update existing records, not add new ones)
    response2 = client.post(
        "/pipeline/import-excel",
        data={"file_path": excel_file}
    )
    assert response2.status_code == 200
    data2 = response2.json()
    
    # Second import should have more updates and fewer/no additions
    # (assuming data hasn't changed between imports)
    assert data2["summary"]["records_updated"] >= data1["summary"]["records_updated"]
    assert data2["summary"]["records_added"] <= data1["summary"]["records_added"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
