# Deduplication Logic Implementation

## Overview

Task 1.2 has been successfully implemented, adding comprehensive deduplication logic to the Excel importer service. The implementation ensures that scheme data can be safely imported multiple times without creating duplicates.

## Implementation Details

### 1. Deduplication Key
- **Primary Key**: `scheme_name` AND `ministry` combination
- This matches the UNIQUE constraint in the `schemes_clean` table
- Ensures that schemes with the same name but different ministries are treated as separate entities

### 2. Core Methods Added

#### `check_existing_scheme(scheme_name, ministry)`
- Queries the database to find existing schemes
- Returns the existing record if found, None otherwise
- Uses Supabase client to query `schemes_clean` table

#### `merge_scheme_data(existing, new)`
- Merges new Excel data with existing database records
- **Merge Strategy**:
  - **Simple fields**: New non-null values override existing values
  - **Array fields**: Union of existing and new values (no duplicates)
  - **Null values**: Existing values preserved when new data is null
  - **Timestamps**: Updated to reflect latest import
  - **ID**: Original database ID is preserved

#### `insert_scheme(scheme_data)`
- Inserts a new scheme record into the database
- Adds timestamp for tracking
- Returns success/failure status

#### `update_scheme(scheme_id, scheme_data)`
- Updates an existing scheme record
- Preserves the original ID
- Returns success/failure status

### 3. Enhanced Import Function

The `import_excel_to_database()` function now supports:
- **Parameter**: `apply_deduplication` (default: True)
- **Returns**: Enhanced summary with:
  - `records_added`: Count of new schemes inserted
  - `records_updated`: Count of existing schemes updated
  - `records_skipped`: Count of schemes that failed to process
  - `records_extracted`: Total schemes extracted from Excel
  - `records_processed`: Total rows processed

### 4. Merge Logic Details

#### Simple Fields (Override Strategy)
These fields are updated if new value is non-null:
- `launch_year`
- `status`
- `category`
- `source_url`
- `funding_type`
- `max_funding_amount`
- `total_budget_allocated`
- `startups_funded_count`
- `dpiit_required`
- `geographic_restriction`
- `application_portal`
- `application_deadline`
- `processing_timeline`
- `success_stories`
- `nlp_summary`

#### Array Fields (Union Strategy)
These fields are merged using set union:
- `sector_eligibility`
- `startup_stage`
- `required_documents`

**Example**:
```
Existing: ['Tech', 'Healthcare']
New:      ['Healthcare', 'Agriculture']
Result:   ['Tech', 'Healthcare', 'Agriculture']
```

## Usage Examples

### Basic Import with Deduplication
```python
from pipeline.excel_importer import import_excel_to_database

result = import_excel_to_database('schemes.xlsx')

print(f"Added: {result['records_added']}")
print(f"Updated: {result['records_updated']}")
print(f"Skipped: {result['records_skipped']}")
```

### Extract Only (No Database Operations)
```python
result = import_excel_to_database('schemes.xlsx', apply_deduplication=False)

schemes = result['schemes']  # List of extracted scheme dictionaries
```

## Deduplication Scenarios

### Scenario 1: Exact Duplicate
- **Existing**: Scheme A | Ministry X
- **New**: Scheme A | Ministry X
- **Action**: MERGE - Data is merged, existing record updated

### Scenario 2: Same Name, Different Ministry
- **Existing**: Scheme A | Ministry X
- **New**: Scheme A | Ministry Y
- **Action**: INSERT - Treated as different scheme

### Scenario 3: Different Name, Same Ministry
- **Existing**: Scheme A | Ministry X
- **New**: Scheme B | Ministry X
- **Action**: INSERT - Treated as different scheme

### Scenario 4: Completely New
- **Existing**: Scheme A | Ministry X
- **New**: Scheme C | Ministry Z
- **Action**: INSERT - No match, new record created

## Testing

### Unit Tests
All tests pass successfully:
- ✓ `test_check_existing_scheme_not_found`
- ✓ `test_merge_scheme_data_simple_fields`
- ✓ `test_merge_scheme_data_preserves_existing_when_new_is_null`
- ✓ `test_merge_scheme_data_array_union`
- ✓ `test_import_without_deduplication`

### Demonstration Script
Run `python pipeline/test_deduplication_demo.py` to see:
- Visual demonstration of merge logic
- Example scenarios with sample data
- Clear explanation of deduplication rules

## Benefits

1. **Idempotent**: Safe to run import multiple times
2. **Data Preservation**: Existing data not lost during updates
3. **Comprehensive**: Handles both simple and complex field types
4. **Flexible**: Can disable deduplication for testing
5. **Traceable**: Detailed logging and error reporting
6. **Robust**: Handles edge cases (null values, empty arrays, etc.)

## Compliance with Requirements

✅ **Requirement 1.3**: Check for existing schemes by scheme_name AND ministry combination
✅ **Requirement 1.3**: Implement merge logic for existing records (preserve most recent data)
✅ **Requirement 1.3**: Insert new records if no match found

## Files Modified

1. `pipeline/excel_importer.py` - Added deduplication methods
2. `tests/test_excel_importer.py` - Added comprehensive test suite
3. `pipeline/test_deduplication_demo.py` - Created demonstration script

## Next Steps

Task 1.2 is complete. The next task (1.3) involves creating an API endpoint for Excel import that will use this deduplication logic.
