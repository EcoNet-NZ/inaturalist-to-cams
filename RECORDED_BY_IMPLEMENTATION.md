# RecordedBy and RecordedDate Implementation

This document describes the implementation of the `RecordedBy` and `RecordedDate` fields in the CAMS Visits table, which track the iNaturalist user who made the most recent observation field update and when that update occurred.

## Overview

The system now captures and stores:
- **RecordedBy**: The iNaturalist username of the user who made the most recent observation field update
- **RecordedDate**: The date and time when the most recent observation field update was made

## Implementation Details

### New Fields Added

#### Database Schema (`config/cams_schema.json`)
```json
"RecordedBy": {
    "name": "RecordedBy",
    "type": "String",
    "length": 128
},
"RecordedDate": {
    "name": "RecordedDate",
    "type": "Date"
}
```

#### Data Model Classes
- `iNatObservation`: Added `recorded_by` and `recorded_date` fields
- `WeedVisit`: Added `recorded_by` and `recorded_date` fields

### Key Components

#### 1. Username Cache (`inat_to_cams/username_cache.py`)
- SQLite-based cache to store iNaturalist user ID to username mappings
- Reduces API calls by caching username lookups
- Automatic fallback to API when username not in cache
- Cache statistics and management functions

#### 2. Enhanced INatReader (`inat_to_cams/inaturalist_reader.py`)
- New method: `get_most_recent_field_update_info(observation)`
- Finds the observation field value with the most recent `updated_at` timestamp
- Extracts username from user object or fetches via cache if only user_id available
- Integrated into the `flatten()` method to populate new fields

#### 3. Updated Data Flow
1. **INatReader** extracts the most recent field update info from iNaturalist observation
2. **Translator** maps the data to CAMS format
3. **CamsWriter** writes the new fields to the CAMS Visits table
4. **CamsReader** reads the fields back when loading existing records

## Usage

### For New Observations
The system automatically captures `RecordedBy` and `RecordedDate` information for all new observations processed through the normal synchronization flow.

### For Existing Records (Migration)
Use the migration script to update existing records:

```bash
# Dry run to see what would be updated
python migration/update_recorded_by_fields.py --dry-run

# Update all records in batches of 25
python migration/update_recorded_by_fields.py --batch-size 25

# Update only first 100 records for testing
python migration/update_recorded_by_fields.py --limit 100

# Combination: dry run with limit
python migration/update_recorded_by_fields.py --dry-run --limit 10
```

### Migration Script Options
- `--dry-run`: Show what would be updated without making changes
- `--batch-size N`: Process N records at a time (default: 50)
- `--limit N`: Limit to N total records (for testing)

## How It Works

### Determining the "Most Recent" Update
The system identifies the most recent observation field update by:
1. **Filtering to tracked fields**: Only examines observation field values that are in the `TRACKED_OBSERVATION_FIELDS` registry
2. **Finding most recent**: Among tracked fields, finds the one with the latest `updated_at` or `created_at` timestamp
3. **Extracting user info**: Gets the user information and timestamp from that specific field value
4. **Fallback logic**: If no tracked fields exist, falls back to observation editor/creator information

### Username Resolution
The system tries multiple approaches to get the username:
1. **Direct user object**: If the observation field value has a `user` object with `login` field
2. **User ID lookup**: If only `user_id` is available, lookup username via cache/API
3. **Fallback**: If username cannot be resolved, uses format `user_{user_id}`

### Fallback Strategy
When no tracked observation fields exist, the system falls back to:
1. **Last editor**: Uses observation's `user` and `updated_at` (most recent edit)
2. **Creator**: Uses observation's `user` and `created_at` (original creation)

### Field Filtering
The system only considers observation fields that are in the `TRACKED_OBSERVATION_FIELDS` registry:
- **Current fields**: All fields actively processed by the application
- **Legacy fields**: Backward compatibility fields for older observations
- **Maintainable**: Single source of truth for field tracking

### Caching Strategy
- Usernames are cached in SQLite database (`inat_username_cache.sqlite`)
- Cache reduces API calls for repeated user lookups
- Cache persists between runs
- Automatic cache management with statistics

## Files Modified

### Core Implementation
- `inat_to_cams/inaturalist_observation.py` - Added new fields to data model
- `inat_to_cams/inaturalist_reader.py` - Added field extraction logic
- `inat_to_cams/translator.py` - Added field mapping
- `inat_to_cams/cams_feature.py` - Added fields to WeedVisit class
- `inat_to_cams/cams_writer.py` - Added fields to write operations
- `inat_to_cams/cams_reader.py` - Added fields to read operations

### New Files
- `inat_to_cams/username_cache.py` - Username caching implementation
- `migration/update_recorded_by_fields.py` - Migration script for existing records

### Configuration
- `config/cams_schema.json` - Added new field definitions

## Testing

A test script is provided to verify the implementation:

```bash
python test_recorded_by_implementation.py
```

This script tests:
- Most recent field update identification
- Username extraction
- Cache functionality
- Edge cases (empty field values, etc.)

## Error Handling

The implementation includes robust error handling:
- Graceful fallback when user information is unavailable
- Logging of errors and warnings
- Continuation of processing even if username lookup fails
- Cache error recovery

## Performance Considerations

- **Username caching** significantly reduces API calls
- **Batch processing** in migration script respects API rate limits
- **Configurable delays** between batches to avoid overwhelming the API
- **Efficient queries** to identify records needing updates

## Monitoring

The system provides logging and statistics:
- Migration progress and results
- Cache hit/miss statistics
- Error counts and details
- Processing summaries

## Maintainer Workflow

### Adding New Observation Fields
When adding a new observation field to the project:

1. **Add the field processing code** (e.g., `get_observation_value()` call)
2. **Update the registry**: Add the field name to `TRACKED_OBSERVATION_FIELDS` in `inaturalist_reader.py`
3. **Run validation**: Execute `python test_recorded_by_implementation.py` to ensure completeness
4. **Test the change**: Verify that the new field is included in RecordedBy tracking

### Validation
The system includes validation to ensure field registry completeness:
```python
# Test field registry completeness
is_complete, missing_fields, extra_fields = INatReader.validate_tracked_fields()
```

### Maintainer Notes in Code
Look for `MAINTAINER NOTE:` comments in the code for guidance on where to make changes.

## Future Enhancements

Potential improvements for future versions:
1. **Field-specific tracking**: Track updates per observation field type
2. **Update history**: Store complete history of field updates
3. **User role information**: Include user roles/permissions from iNaturalist
4. **Bulk cache warming**: Pre-populate cache with common users
5. **Cache expiration**: Add TTL for cached usernames to handle username changes
6. **Automated field discovery**: Scan code to automatically detect new fields
