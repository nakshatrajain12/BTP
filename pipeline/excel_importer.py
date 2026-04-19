"""
Excel Importer Service for Dashboard Enhancements V2

This module handles importing scheme data from Excel files and mapping
them to the schemes_clean table schema with proper data type conversions
and deduplication logic.

Features:
- Parses Excel files with scheme data
- Maps Excel columns to database schema fields
- Handles data type conversions:
  * Currency values (float) to integers
  * Semicolon-separated strings to arrays
  * Date parsing with special handling for "Rolling basis" text
  * Processing timeline conversion (days to string format)
- Validates required fields (scheme_name, ministry)
- Deduplication by scheme_name AND ministry combination
- Merges new data with existing records (preserves most recent data)
- Inserts new records if no match found
- Comprehensive error handling and logging

Usage:
    from pipeline.excel_importer import import_excel_to_database
    
    # Import with deduplication (default)
    result = import_excel_to_database('path/to/excel_file.xlsx')
    
    # Import without deduplication (extract only)
    result = import_excel_to_database('path/to/excel_file.xlsx', apply_deduplication=False)
    
    if result['success']:
        print(f"Extracted: {result['records_extracted']}")
        print(f"Added: {result['records_added']}")
        print(f"Updated: {result['records_updated']}")
    else:
        print(f"Errors: {result['errors']}")

Deduplication Strategy:
- Checks for existing schemes by scheme_name AND ministry combination
- If match found: merges new data with existing (non-null values override)
- If no match: inserts as new record
- Array fields (sectors, stages, documents) are merged using union
- Timestamps are updated to reflect latest import

Column Mapping:
    Excel Column                    -> Database Column
    -----------------------------------------------
    scheme_name                     -> scheme_name
    ministry                        -> ministry
    max_funding_amount_INR          -> max_funding_amount
    total_budget_allocated_INR      -> total_budget_allocated
    processing_timeline_days        -> processing_timeline
    success_stories_notes           -> success_stories
    (and more - see COLUMN_MAPPING in ExcelImporter class)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from pipeline.schemas import SchemeRecord
from scrapers.base_scraper import supabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExcelImporter:
    """Handles Excel file parsing and data import to schemes_clean table."""
    
    # Column mapping from Excel to database schema
    COLUMN_MAPPING = {
        'scheme_name': 'scheme_name',
        'ministry': 'ministry',
        'launch_year': 'launch_year',
        'status': 'status',
        'category': 'category',
        'source_url': 'source_url',
        'funding_type': 'funding_type',
        'max_funding_amount_INR': 'max_funding_amount',
        'total_budget_allocated_INR': 'total_budget_allocated',
        'startups_funded_count': 'startups_funded_count',
        'sector_eligibility': 'sector_eligibility',
        'startup_stage': 'startup_stage',
        'dpiit_required': 'dpiit_required',
        'geographic_restriction': 'geographic_restriction',
        'application_portal': 'application_portal',
        'application_deadline': 'application_deadline',
        'processing_timeline_days': 'processing_timeline',
        'required_documents': 'required_documents',
        'success_stories_notes': 'success_stories',
        'nlp_summary': 'nlp_summary'
    }
    
    def __init__(self, excel_path: str):
        """
        Initialize the Excel importer.
        
        Args:
            excel_path: Path to the Excel file to import
        """
        self.excel_path = excel_path
        self.df = None
        self.errors = []
        
    def parse_excel(self) -> bool:
        """
        Parse the Excel file into a pandas DataFrame.
        
        Returns:
            True if parsing successful, False otherwise
        """
        try:
            self.df = pd.read_excel(self.excel_path)
            logger.info(f"Successfully parsed Excel file: {self.excel_path}")
            logger.info(f"Found {len(self.df)} rows")
            return True
        except Exception as e:
            logger.error(f"Failed to parse Excel file: {e}")
            self.errors.append(f"Excel parsing error: {str(e)}")
            return False
    
    def _parse_array_field(self, value: Any) -> List[str]:
        """
        Parse semicolon-separated string into array.
        
        Args:
            value: String value with semicolons or list
            
        Returns:
            List of strings
        """
        if pd.isna(value) or value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            # Split by semicolon and clean up whitespace
            return [item.strip() for item in value.split(';') if item.strip()]
        return []
    
    def _parse_date(self, value: Any) -> Optional[date]:
        """
        Parse date field handling various formats.
        
        Args:
            value: Date value in various formats
            
        Returns:
            date object or None
        """
        if pd.isna(value) or value is None:
            return None
        
        # Handle "Rolling basis" or similar text
        if isinstance(value, str):
            value_lower = value.lower()
            if 'rolling' in value_lower or 'ongoing' in value_lower or 'open' in value_lower:
                return None
            
            # Try to parse date string
            try:
                parsed = pd.to_datetime(value)
                return parsed.date()
            except:
                return None
        
        # Handle datetime objects
        if isinstance(value, (datetime, pd.Timestamp)):
            return value.date()
        
        return None
    
    def _parse_processing_timeline(self, value: Any) -> Optional[str]:
        """
        Convert processing_timeline_days to string format.
        
        Args:
            value: Number of days or string
            
        Returns:
            String representation like "45 days" or None
        """
        if pd.isna(value) or value is None:
            return None
        
        if isinstance(value, (int, float)):
            days = int(value)
            return f"{days} days"
        
        return str(value)
    
    def _convert_currency_to_int(self, value: Any) -> Optional[int]:
        """
        Convert currency values to integers.
        
        Args:
            value: Float or int currency value
            
        Returns:
            Integer value or None
        """
        if pd.isna(value) or value is None:
            return None
        
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _map_row_to_scheme(self, row: pd.Series, row_index: int) -> Optional[Dict[str, Any]]:
        """
        Map a single Excel row to scheme data dictionary.
        
        Args:
            row: Pandas Series representing one row
            row_index: Row index for error reporting
            
        Returns:
            Dictionary with mapped data or None if invalid
        """
        try:
            scheme_data = {}
            
            # Map each field with appropriate conversion
            for excel_col, db_col in self.COLUMN_MAPPING.items():
                if excel_col not in row.index:
                    continue
                
                value = row[excel_col]
                
                # Handle array fields
                if db_col in ['sector_eligibility', 'startup_stage', 'required_documents']:
                    scheme_data[db_col] = self._parse_array_field(value)
                
                # Handle date fields
                elif db_col == 'application_deadline':
                    scheme_data[db_col] = self._parse_date(value)
                
                # Handle processing timeline
                elif db_col == 'processing_timeline':
                    scheme_data[db_col] = self._parse_processing_timeline(value)
                
                # Handle currency fields
                elif db_col in ['max_funding_amount', 'total_budget_allocated']:
                    scheme_data[db_col] = self._convert_currency_to_int(value)
                
                # Handle count fields
                elif db_col == 'startups_funded_count':
                    if not pd.isna(value):
                        scheme_data[db_col] = int(value) if value else None
                    else:
                        scheme_data[db_col] = None
                
                # Handle boolean fields
                elif db_col == 'dpiit_required':
                    if pd.isna(value):
                        scheme_data[db_col] = None
                    else:
                        scheme_data[db_col] = bool(value)
                
                # Handle string fields
                else:
                    if pd.isna(value) or value is None:
                        scheme_data[db_col] = None
                    else:
                        scheme_data[db_col] = str(value)
            
            # Validate required fields
            if not scheme_data.get('scheme_name'):
                self.errors.append(f"Row {row_index}: Missing scheme_name")
                return None
            
            if not scheme_data.get('ministry'):
                self.errors.append(f"Row {row_index}: Missing ministry")
                return None
            
            # Convert date to ISO string for database
            if scheme_data.get('application_deadline'):
                scheme_data['application_deadline'] = scheme_data['application_deadline'].isoformat()
            
            return scheme_data
            
        except Exception as e:
            self.errors.append(f"Row {row_index}: Error mapping data - {str(e)}")
            logger.error(f"Error mapping row {row_index}: {e}")
            return None
    
    def extract_schemes(self) -> List[Dict[str, Any]]:
        """
        Extract all scheme records from the parsed DataFrame.
        
        Returns:
            List of scheme data dictionaries
        """
        if self.df is None:
            logger.error("No DataFrame loaded. Call parse_excel() first.")
            return []
        
        schemes = []
        for idx, row in self.df.iterrows():
            scheme_data = self._map_row_to_scheme(row, idx)
            if scheme_data:
                schemes.append(scheme_data)
        
        logger.info(f"Successfully extracted {len(schemes)} schemes from {len(self.df)} rows")
        if self.errors:
            logger.warning(f"Encountered {len(self.errors)} errors during extraction")
        
        return schemes
    
    def get_errors(self) -> List[str]:
        """
        Get list of errors encountered during import.
        
        Returns:
            List of error messages
        """
        return self.errors


    def check_existing_scheme(self, scheme_name: str, ministry: str) -> Optional[Dict[str, Any]]:
        """
        Check if a scheme already exists in the database by scheme_name and ministry.
        
        Args:
            scheme_name: Name of the scheme
            ministry: Ministry name
            
        Returns:
            Existing scheme record or None if not found
        """
        try:
            response = supabase.table('schemes_clean').select('*').eq(
                'scheme_name', scheme_name
            ).eq('ministry', ministry).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error checking existing scheme: {e}")
            return None
    
    def merge_scheme_data(self, existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge new scheme data with existing data, preserving most recent information.
        
        Strategy:
        - Non-null new values override existing values
        - Arrays are merged (union of values)
        - Numeric values use new if provided, else keep existing
        - Timestamps are updated to current time
        
        Args:
            existing: Existing scheme record from database
            new: New scheme data from Excel
            
        Returns:
            Merged scheme data dictionary
        """
        merged = existing.copy()
        
        # Fields to merge with preference for new non-null values
        simple_fields = [
            'launch_year', 'status', 'category', 'source_url', 'funding_type',
            'max_funding_amount', 'total_budget_allocated', 'startups_funded_count',
            'dpiit_required', 'geographic_restriction', 'application_portal',
            'application_deadline', 'processing_timeline', 'success_stories', 'nlp_summary'
        ]
        
        for field in simple_fields:
            if field in new and new[field] is not None:
                merged[field] = new[field]
        
        # Merge array fields (union of values)
        array_fields = ['sector_eligibility', 'startup_stage', 'required_documents']
        for field in array_fields:
            if field in new and new[field]:
                existing_values = set(existing.get(field) or [])
                new_values = set(new[field])
                merged[field] = list(existing_values.union(new_values))
        
        # Update timestamp
        merged['last_scraped_at'] = datetime.now().isoformat()
        
        return merged
    
    def insert_scheme(self, scheme_data: Dict[str, Any]) -> bool:
        """
        Insert a new scheme into the database.
        
        Args:
            scheme_data: Scheme data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add timestamp
            scheme_data['last_scraped_at'] = datetime.now().isoformat()
            
            response = supabase.table('schemes_clean').insert(scheme_data).execute()
            return True
        except Exception as e:
            logger.error(f"Error inserting scheme '{scheme_data.get('scheme_name')}': {e}")
            self.errors.append(f"Insert error for '{scheme_data.get('scheme_name')}': {str(e)}")
            return False
    
    def update_scheme(self, scheme_id: str, scheme_data: Dict[str, Any]) -> bool:
        """
        Update an existing scheme in the database.
        
        Args:
            scheme_id: UUID of the scheme to update
            scheme_data: Updated scheme data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove id from update data
            update_data = {k: v for k, v in scheme_data.items() if k != 'id'}
            
            response = supabase.table('schemes_clean').update(update_data).eq('id', scheme_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating scheme '{scheme_data.get('scheme_name')}': {e}")
            self.errors.append(f"Update error for '{scheme_data.get('scheme_name')}': {str(e)}")
            return False


def import_excel_to_database(excel_path: str, apply_deduplication: bool = True) -> Dict[str, Any]:
    """
    Import Excel file data into schemes_clean table with deduplication.
    
    This function handles the complete import process including:
    - Parsing the Excel file
    - Mapping columns to database schema
    - Data type conversions
    - Deduplication by scheme_name and ministry
    - Merging with existing records
    - Error handling
    
    Args:
        excel_path: Path to the Excel file
        apply_deduplication: If True, check for duplicates and merge; if False, just extract
        
    Returns:
        Dictionary with import summary:
        - success: bool
        - records_processed: int
        - records_extracted: int
        - records_added: int
        - records_updated: int
        - records_skipped: int
        - errors: List[str]
    """
    importer = ExcelImporter(excel_path)
    
    # Parse Excel file
    if not importer.parse_excel():
        return {
            'success': False,
            'records_processed': 0,
            'records_extracted': 0,
            'records_added': 0,
            'records_updated': 0,
            'records_skipped': 0,
            'errors': importer.get_errors()
        }
    
    # Extract schemes
    schemes = importer.extract_schemes()
    
    # If deduplication not requested, return extracted data only
    if not apply_deduplication:
        return {
            'success': True,
            'records_processed': len(importer.df) if importer.df is not None else 0,
            'records_extracted': len(schemes),
            'schemes': schemes,
            'records_added': 0,
            'records_updated': 0,
            'records_skipped': 0,
            'errors': importer.get_errors()
        }
    
    # Apply deduplication and insert/update
    records_added = 0
    records_updated = 0
    records_skipped = 0
    
    for scheme in schemes:
        scheme_name = scheme.get('scheme_name')
        ministry = scheme.get('ministry')
        
        # Check for existing scheme
        existing = importer.check_existing_scheme(scheme_name, ministry)
        
        if existing:
            # Merge and update
            merged_data = importer.merge_scheme_data(existing, scheme)
            if importer.update_scheme(existing['id'], merged_data):
                records_updated += 1
                logger.info(f"Updated scheme: {scheme_name} ({ministry})")
            else:
                records_skipped += 1
        else:
            # Insert new scheme
            if importer.insert_scheme(scheme):
                records_added += 1
                logger.info(f"Added new scheme: {scheme_name} ({ministry})")
            else:
                records_skipped += 1
    
    return {
        'success': True,
        'records_processed': len(importer.df) if importer.df is not None else 0,
        'records_extracted': len(schemes),
        'records_added': records_added,
        'records_updated': records_updated,
        'records_skipped': records_skipped,
        'errors': importer.get_errors()
    }


if __name__ == "__main__":
    # Test the importer with the provided Excel file
    excel_file = "Central_Govt_Startup_Schemes_Database.xlsx"
    
    if not os.path.exists(excel_file):
        print(f"Error: Excel file not found: {excel_file}")
        sys.exit(1)
    
    print(f"Importing data from {excel_file} with deduplication...")
    result = import_excel_to_database(excel_file, apply_deduplication=True)
    
    print(f"\n{'='*60}")
    print("IMPORT SUMMARY")
    print(f"{'='*60}")
    print(f"Success: {result['success']}")
    print(f"Records Processed: {result['records_processed']}")
    print(f"Records Extracted: {result['records_extracted']}")
    print(f"Records Added: {result['records_added']}")
    print(f"Records Updated: {result['records_updated']}")
    print(f"Records Skipped: {result['records_skipped']}")
    print(f"Errors: {len(result['errors'])}")
    
    if result['errors']:
        print(f"\nErrors encountered:")
        for error in result['errors'][:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(result['errors']) > 10:
            print(f"  ... and {len(result['errors']) - 10} more errors")
