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
1. Examining all observation field values (`ofvs`) in the iNaturalist observation
2. Finding the one with the latest `updated_at` or `created_at` timestamp
3. Extracting the user information and timestamp from that field value

### Username Resolution
The system tries multiple approaches to get the username:
1. **Direct user object**: If the observation field value has a `user` object with `login` field
2. **User ID lookup**: If only `user_id` is available, lookup username via cache/API
3. **Fallback**: If username cannot be resolved, uses format `user_{user_id}`

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

## Future Enhancements

Potential improvements for future versions:
1. **Field-specific tracking**: Track updates per observation field type
2. **Update history**: Store complete history of field updates
3. **User role information**: Include user roles/permissions from iNaturalist
4. **Bulk cache warming**: Pre-populate cache with common users
5. **Cache expiration**: Add TTL for cached usernames to handle username changes
