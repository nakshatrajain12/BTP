"""
Unit tests for Excel Importer Service
"""

import pytest
import pandas as pd
from datetime import date
from pipeline.excel_importer import ExcelImporter, import_excel_to_database


class TestExcelImporter:
    """Test suite for ExcelImporter class"""
    
    def test_parse_array_field_with_semicolons(self):
        """Test parsing semicolon-separated strings into arrays"""
        importer = ExcelImporter("test.xlsx")
        
        # Test normal semicolon-separated string
        result = importer._parse_array_field("Agriculture; Biotech; Social Impact")
        assert result == ["Agriculture", "Biotech", "Social Impact"]
        
        # Test with extra whitespace
        result = importer._parse_array_field("  Tech  ;  Finance  ;  Healthcare  ")
        assert result == ["Tech", "Finance", "Healthcare"]
        
        # Test empty string
        result = importer._parse_array_field("")
        assert result == []
        
        # Test None
        result = importer._parse_array_field(None)
        assert result == []
        
        # Test NaN
        result = importer._parse_array_field(pd.NA)
        assert result == []
    
    def test_parse_date_with_various_formats(self):
        """Test date parsing with different input formats"""
        importer = ExcelImporter("test.xlsx")
        
        # Test "Rolling basis" text
        result = importer._parse_date("Rolling basis")
        assert result is None
        
        # Test "Ongoing" text
        result = importer._parse_date("ongoing")
        assert result is None
        
        # Test None
        result = importer._parse_date(None)
        assert result is None
        
        # Test datetime object
        from datetime import datetime
        dt = datetime(2024, 12, 31)
        result = importer._parse_date(dt)
        assert result == date(2024, 12, 31)
    
    def test_parse_processing_timeline(self):
        """Test processing timeline conversion"""
        importer = ExcelImporter("test.xlsx")
        
        # Test integer days
        result = importer._parse_processing_timeline(45)
        assert result == "45 days"
        
        # Test float days
        result = importer._parse_processing_timeline(30.0)
        assert result == "30 days"
        
        # Test None
        result = importer._parse_processing_timeline(None)
        assert result is None
        
        # Test string
        result = importer._parse_processing_timeline("2-3 weeks")
        assert result == "2-3 weeks"
    
    def test_convert_currency_to_int(self):
        """Test currency conversion to integers"""
        importer = ExcelImporter("test.xlsx")
        
        # Test float
        result = importer._convert_currency_to_int(5000000.0)
        assert result == 5000000
        
        # Test integer
        result = importer._convert_currency_to_int(2000000)
        assert result == 2000000
        
        # Test None
        result = importer._convert_currency_to_int(None)
        assert result is None
        
        # Test NaN
        result = importer._convert_currency_to_int(pd.NA)
        assert result is None
    
    def test_map_row_to_scheme_with_valid_data(self):
        """Test mapping a valid row to scheme data"""
        importer = ExcelImporter("test.xlsx")
        
        row = pd.Series({
            'scheme_name': 'Test Scheme',
            'ministry': 'Test Ministry',
            'launch_year': 2021,
            'status': 'Active',
            'category': 'Funding',
            'source_url': 'https://example.com',
            'funding_type': 'Grant',
            'max_funding_amount_INR': 5000000.0,
            'total_budget_allocated_INR': 100000000.0,
            'startups_funded_count': 100.0,
            'sector_eligibility': 'Tech; Finance',
            'startup_stage': 'Idea; Prototype',
            'dpiit_required': True,
            'geographic_restriction': 'Pan India',
            'application_portal': 'https://apply.example.com',
            'application_deadline': 'Rolling basis',
            'processing_timeline_days': 30.0,
            'required_documents': 'Doc1; Doc2',
            'success_stories_notes': 'Success story text',
            'nlp_summary': 'Summary text'
        })
        
        result = importer._map_row_to_scheme(row, 0)
        
        assert result is not None
        assert result['scheme_name'] == 'Test Scheme'
        assert result['ministry'] == 'Test Ministry'
        assert result['max_funding_amount'] == 5000000
        assert result['sector_eligibility'] == ['Tech', 'Finance']
        assert result['startup_stage'] == ['Idea', 'Prototype']
        assert result['processing_timeline'] == '30 days'
        assert result['dpiit_required'] is True
    
    def test_map_row_to_scheme_missing_required_fields(self):
        """Test that rows with missing required fields are rejected"""
        importer = ExcelImporter("test.xlsx")
        
        # Missing scheme_name
        row1 = pd.Series({
            'scheme_name': None,
            'ministry': 'Test Ministry'
        })
        result1 = importer._map_row_to_scheme(row1, 0)
        assert result1 is None
        assert len(importer.errors) > 0
        
        # Reset errors
        importer.errors = []
        
        # Missing ministry
        row2 = pd.Series({
            'scheme_name': 'Test Scheme',
            'ministry': None
        })
        result2 = importer._map_row_to_scheme(row2, 1)
        assert result2 is None
        assert len(importer.errors) > 0
    
    def test_extract_schemes_from_dataframe(self):
        """Test extracting multiple schemes from a DataFrame"""
        importer = ExcelImporter("test.xlsx")
        
        # Create test DataFrame
        importer.df = pd.DataFrame([
            {
                'scheme_name': 'Scheme 1',
                'ministry': 'Ministry 1',
                'category': 'Funding',
                'source_url': 'https://example1.com'
            },
            {
                'scheme_name': 'Scheme 2',
                'ministry': 'Ministry 2',
                'category': 'Incubation',
                'source_url': 'https://example2.com'
            },
            {
                'scheme_name': None,  # Invalid - missing name
                'ministry': 'Ministry 3',
                'category': 'Tax Benefit',
                'source_url': 'https://example3.com'
            }
        ])
        
        schemes = importer.extract_schemes()
        
        # Should extract 2 valid schemes, skip 1 invalid
        assert len(schemes) == 2
        assert schemes[0]['scheme_name'] == 'Scheme 1'
        assert schemes[1]['scheme_name'] == 'Scheme 2'
        assert len(importer.errors) == 1


class TestImportExcelToDatabase:
    """Test suite for the main import function"""
    
    def test_import_with_nonexistent_file(self):
        """Test import with a file that doesn't exist"""
        result = import_excel_to_database("nonexistent_file.xlsx")
        
        assert result['success'] is False
        assert result['records_processed'] == 0
        assert result['records_extracted'] == 0
        assert len(result['errors']) > 0
    
    def test_import_with_valid_file(self):
        """Test import with the actual Excel file"""
        import os
        
        excel_file = "Central_Govt_Startup_Schemes_Database.xlsx"
        
        # Skip if file doesn't exist in test environment
        if not os.path.exists(excel_file):
            pytest.skip("Excel file not found in test environment")
        
        result = import_excel_to_database(excel_file, apply_deduplication=False)
        
        assert result['success'] is True
        assert result['records_processed'] > 0
        assert result['records_extracted'] > 0
        assert 'schemes' in result
        
        # Verify first scheme has required fields
        if result['schemes']:
            first_scheme = result['schemes'][0]
            assert 'scheme_name' in first_scheme
            assert 'ministry' in first_scheme
            assert first_scheme['scheme_name'] is not None
            assert first_scheme['ministry'] is not None


class TestDeduplicationLogic:
    """Test suite for deduplication functionality"""
    
    def test_check_existing_scheme_not_found(self):
        """Test checking for a scheme that doesn't exist"""
        importer = ExcelImporter("test.xlsx")
        
        # Use a scheme name that definitely doesn't exist
        result = importer.check_existing_scheme(
            "NonExistent Scheme XYZ123", 
            "NonExistent Ministry XYZ123"
        )
        
        assert result is None
    
    def test_merge_scheme_data_simple_fields(self):
        """Test merging scheme data with simple field updates"""
        importer = ExcelImporter("test.xlsx")
        
        existing = {
            'id': 'test-uuid-123',
            'scheme_name': 'Test Scheme',
            'ministry': 'Test Ministry',
            'launch_year': 2020,
            'status': 'Active',
            'category': 'Funding',
            'max_funding_amount': 1000000,
            'sector_eligibility': ['Tech'],
            'startup_stage': ['Idea']
        }
        
        new = {
            'scheme_name': 'Test Scheme',
            'ministry': 'Test Ministry',
            'launch_year': 2021,  # Updated year
            'status': 'Active',
            'category': 'Funding',
            'max_funding_amount': 2000000,  # Updated amount
            'sector_eligibility': ['Finance'],  # New sector
            'startup_stage': ['Prototype']  # New stage
        }
        
        merged = importer.merge_scheme_data(existing, new)
        
        # Simple fields should be updated
        assert merged['launch_year'] == 2021
        assert merged['max_funding_amount'] == 2000000
        
        # Array fields should be merged (union)
        assert set(merged['sector_eligibility']) == {'Tech', 'Finance'}
        assert set(merged['startup_stage']) == {'Idea', 'Prototype'}
        
        # ID should be preserved
        assert merged['id'] == 'test-uuid-123'
        
        # Timestamp should be updated
        assert 'last_scraped_at' in merged
    
    def test_merge_scheme_data_preserves_existing_when_new_is_null(self):
        """Test that existing values are preserved when new values are null"""
        importer = ExcelImporter("test.xlsx")
        
        existing = {
            'id': 'test-uuid-456',
            'scheme_name': 'Test Scheme',
            'ministry': 'Test Ministry',
            'max_funding_amount': 5000000,
            'processing_timeline': '30 days',
            'success_stories': 'Existing success story'
        }
        
        new = {
            'scheme_name': 'Test Scheme',
            'ministry': 'Test Ministry',
            'max_funding_amount': None,  # Null value
            'processing_timeline': None,  # Null value
            'success_stories': 'New success story'  # Non-null value
        }
        
        merged = importer.merge_scheme_data(existing, new)
        
        # Existing values should be preserved when new is null
        assert merged['max_funding_amount'] == 5000000
        assert merged['processing_timeline'] == '30 days'
        
        # Non-null new value should override
        assert merged['success_stories'] == 'New success story'
    
    def test_merge_scheme_data_array_union(self):
        """Test that array fields are properly merged using union"""
        importer = ExcelImporter("test.xlsx")
        
        existing = {
            'id': 'test-uuid-789',
            'scheme_name': 'Test Scheme',
            'ministry': 'Test Ministry',
            'sector_eligibility': ['Tech', 'Finance', 'Healthcare'],
            'startup_stage': ['Idea', 'Prototype'],
            'required_documents': ['Doc1', 'Doc2']
        }
        
        new = {
            'scheme_name': 'Test Scheme',
            'ministry': 'Test Ministry',
            'sector_eligibility': ['Finance', 'Agriculture'],  # Overlap + new
            'startup_stage': ['Prototype', 'Early Revenue'],  # Overlap + new
            'required_documents': ['Doc2', 'Doc3']  # Overlap + new
        }
        
        merged = importer.merge_scheme_data(existing, new)
        
        # Should have union of all values
        assert set(merged['sector_eligibility']) == {'Tech', 'Finance', 'Healthcare', 'Agriculture'}
        assert set(merged['startup_stage']) == {'Idea', 'Prototype', 'Early Revenue'}
        assert set(merged['required_documents']) == {'Doc1', 'Doc2', 'Doc3'}
    
    def test_import_without_deduplication(self):
        """Test import with deduplication disabled"""
        import os
        
        excel_file = "Central_Govt_Startup_Schemes_Database.xlsx"
        
        if not os.path.exists(excel_file):
            pytest.skip("Excel file not found in test environment")
        
        result = import_excel_to_database(excel_file, apply_deduplication=False)
        
        assert result['success'] is True
        assert result['records_added'] == 0
        assert result['records_updated'] == 0
        assert result['records_skipped'] == 0
        assert 'schemes' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
