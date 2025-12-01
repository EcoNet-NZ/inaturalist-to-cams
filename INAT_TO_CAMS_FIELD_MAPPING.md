# iNaturalist to CAMS Field Mapping

This document describes the mapping between iNaturalist observation fields and CAMS (Conservation Activity Management System) fields.

## Overview

The synchronization process transforms iNaturalist observations into CAMS features, which consist of:
- **WeedLocation**: The parent feature representing the weed location
- **WeedVisit**: Child records representing individual visits/updates to that location
- **Geometry**: Geographic point data (latitude/longitude)

## Core iNaturalist Fields

### Observation Metadata

| iNaturalist Field | CAMS Table | CAMS Field | Notes |
|------------------|------------|------------|-------|
| `id` | Visits_Table | `iNatRef` | Stored as string |
| `observed_on` | WeedLocations | `DateDiscovered` | Date first observed (initial sync only) |
| `observed_on` or `created_at` | - | - | Fallback to created_at if observed_on missing |
| `updated_at` or `created_at` | Visits_Table | `RecordedDate` | Timestamp of last update |
| `description` | Visits_Table | `Notes` | HTML sanitized; invalid URLs replaced with warning |
| `quality_grade` | Visits_Table | `ObservationQuality` | Values: needs_id, casual, research |

### Geographic Data

| iNaturalist Field | CAMS Table | CAMS Field | Notes |
|------------------|------------|------------|-------|
| `location[1]` (longitude) | Geometry | `x` | WGS84 (WKID 4326) |
| `location[0]` (latitude) | Geometry | `y` | WGS84 (WKID 4326) |
| `location[1]` | WeedLocations | `iNatLongitude` | Stored separately for reference |
| `location[0]` | WeedLocations | `iNatLatitude` | Stored separately for reference |
| `positional_accuracy` | WeedLocations | `LocationAccuracy` | Accuracy in meters |

### Taxon Information

| iNaturalist Field | CAMS Table | CAMS Field | Notes |
|------------------|------------|------------|-------|
| `taxon.ancestor_ids` | WeedLocations | `SpeciesDropDown` | Mapped via taxon_mapping.json; walks lineage to find match |
| `taxon.preferred_common_name` | WeedLocations | `OtherWeedDetails` | Used when taxon unmapped; combined with scientific name |
| `taxon.name` | WeedLocations | `OtherWeedDetails` | Scientific name; used when taxon unmapped |

### Photo Data

| iNaturalist Field | CAMS Table | CAMS Field | Notes |
|------------------|------------|------------|-------|
| `photos[0-4].url` | WeedLocations | `ImageURLs` | Up to 5 photos; square replaced with large; comma-separated |
| `photos[0].attribution` | WeedLocations | `ImageAttribution` | Attribution for first photo |

### External Reference

| iNaturalist Field | CAMS Table | CAMS Field | Notes |
|------------------|------------|------------|-------|
| Constructed URL | WeedLocations | `iNatURL` | https://www.inaturalist.org/observations/{id} |
| Constructed URL | Visits_Table | `iNaturalistURL` | https://www.inaturalist.org/observations/{id} |

## iNaturalist Observation Fields

These are custom observation fields defined in iNaturalist projects.

### Location & Site Information

| iNaturalist Field | CAMS Table | CAMS Field | Notes |
|------------------|------------|------------|-------|
| `Location details` | WeedLocations | `LocationInfo` | Text description of location |
| `Site difficulty` | Visits_Table | `SiteDifficulty` | Values: 1 Easy, 2 Moderate, 3 Challenging, 4 Advanced, 5 Professional |
| `Radius (m) of area surveyed` | Visits_Table | `CheckedNearbyRadius` | Radius in meters |

### Plant Measurements

| iNaturalist Field | CAMS Table | CAMS Field | Notes |
|------------------|------------|------------|-------|
| `Height (m)` | Visits_Table | `Height` | Height in meters |
| `Area in square meters` | Visits_Table | `Area` | Area in square meters |
| `Plant phenology->most common flowering/fruiting reproductive stage` | Visits_Table | `Flowering` | Values: not recorded, vegetative only, flower buds, flowers, immature fruit, mature fruit, seed dispersed |

### Treatment Information

| iNaturalist Field | CAMS Table | CAMS Field | Notes |
|------------------|------------|------------|-------|
| `Treated ?` | Visits_Table | `Treated` | Values: Yes, No, Unknown, Not Yet, Partially |
| `How treated` | Visits_Table | `HowTreated` | Treatment method (e.g., Cut but roots remain, Pulled or dug, etc.) |
| `Treatment substance` | Visits_Table | `TreatmentSubstance` | Herbicide/treatment used; "None" converted to null |
| `Treatment details` | Visits_Table | `TreatmentDetails` | Additional treatment notes |
| `Date controlled` | - | - | Used to calculate visit date and status |

### Status & Follow-up

| iNaturalist Field | CAMS Table | CAMS Field | Notes |
|------------------|------------|------------|-------|
| `Status update` | - | - | Values: Dead / Not Present, Duplicate; used to calculate visit status |
| `Date of status update` | - | - | Used to calculate visit date and status |
| `Date for next visit` | Visits_Table | `DateForReturnVisit` | Planned follow-up date |
| `Effort to control` | WeedLocations | `Urgency` | Integer 1-5; first character extracted; default 1 (initial sync only) |

### User Tracking

| iNaturalist Field | CAMS Table | CAMS Field | Notes |
|------------------|------------|------------|-------|
| `ofv.user.id` (from winning field) | Visits_Table | `RecordedByUserId` | User ID of person who updated winning field; stored as string |
| `ofv.user.login` (from winning field) | Visits_Table | `RecordedByUserName` | Username of person who updated winning field |
| `user.id` (observation owner) | Visits_Table | `RecordedByUserId` | Fallback if no winning field user found |
| `user.login` (observation owner) | Visits_Table | `RecordedByUserName` | Fallback if no winning field username found |

## Calculated Fields

These fields are derived from multiple iNaturalist fields through business logic.

### Visit Date Calculation

The visit date is determined by the latest of:
1. `Date controlled` - if present
2. `Date of status update` - if present
3. `observed_on` - fallback

**Logic:**
- If both date fields present, use the later one
- The "winning field" determines which user is recorded as RecordedBy

### Visit Status Calculation

| Condition | CAMS Visit Status | CAMS CurrentStatus |
|-----------|------------------|-------------------|
| Visit date = Date controlled AND How treated = "Cut but roots remain" | ORANGE | OrangeDeadHeaded |
| Visit date = Date controlled AND Treated = "Yes" | YELLOW | YellowKilledThisYear |
| Visit date = Date of status update AND Status update = "Dead / Not Present" | GREEN | GreenNoRegrowthThisYear |
| Visit date = Date of status update AND Status update = "Duplicate" | GRAY | GrayDuplicate |
| Default | RED | RedGrowth |

### Data Source

| Value | CAMS Table | CAMS Field | Notes |
|-------|------------|------------|-------|
| `iNaturalist_v2` | WeedLocations | `SiteSource` | Hardcoded constant |

## Legacy Field Support

For backward compatibility with older iNaturalist projects:

### Legacy WMANZ Fields

| Legacy Field | Modern Equivalent | Conversion |
|-------------|------------------|------------|
| `Follow-up (YYYY-MM)` | `Date for next visit` | Append "-01" to create full date |
| `Is the pest controlled?` = "yes" | `Treated ?` = "Yes" | Direct mapping |
| `dead or alive?` = "dead" | `Treated ?` = "Yes" | Direct mapping |

### Legacy OMB Wellington Fields

| Legacy Field | Modern Equivalent | Conversion |
|-------------|------------------|------------|
| `Adult Area` | `Area in square meters` | Direct mapping |
| `area of infestation (m2)` | `Area in square meters` | Direct mapping |
| `Professional assistance required` = "yes" | `Site difficulty` = "5 Professional skills required" | Direct mapping |
| `fruiting` = "yes" | `Plant phenology` = "mature fruit" | Direct mapping |
| `Flowering` = "yes" | `Plant phenology` = "flowers" | Direct mapping |

## Field Update Behavior

### Initial Sync Only (WeedLocation)

These fields are only set when creating a new WeedLocation and are **not** updated on subsequent syncs:
- `DateDiscovered` (observed_on)
- `Urgency` (effort_to_control)

### Always Updated (WeedLocation)

These fields are updated on every sync:
- `iNatLongitude`
- `iNatLatitude`
- `LocationAccuracy`
- `ImageURLs`
- `ImageAttribution`
- `iNatURL`

### Visit-Specific (WeedVisit)

These fields are always written to the new/updated WeedVisit:
- All Visits_Table fields are updated with each sync
- A new WeedVisit record is created if the observation has changed

## Special Handling

### HTML Sanitization

The `description` field undergoes HTML sanitization:
- URLs containing `=` characters are removed
- Replaced with: `(INVALID URL DETECTED - see iNaturalist link for full notes)`
- See issue #86 for details

### Treatment Substance

The value "None" is explicitly converted to `null` to distinguish from no value.

### Unmapped Taxa

When a taxon is not found in `taxon_mapping.json`:
- `SpeciesDropDown` is set to "OTHER"
- `OtherWeedDetails` is populated with:
  - Preferred common name + scientific name (if both available)
  - Scientific name only (if common name not available)
  - "Unknown species from iNaturalist" (if neither available)

### Winning Field Logic

The "winning field" (Date controlled vs Date of status update) determines:
1. The `DateCheck` (date_visit_made)
2. The `WeedVisitStatus` (visit_status)
3. The `RecordedByUserId` and `RecordedByUserName` (from the field's updater)

## CAMS Field Name Reference

### WeedLocations Table

| Display Name | Internal Name | Type |
|-------------|--------------|------|
| Date First Observed | DateDiscovered | Date |
| Species | SpeciesDropDown | String(256) |
| Other Weed Details | OtherWeedDetails | String(256) |
| DataSource | SiteSource | String(39) |
| Location details | LocationInfo | String(256) |
| Effort to control | Urgency | Integer(1-5) |
| CurrentStatus | ParentStatusWithDomain | String(80) |
| iNaturalistURL | iNatURL | String(256) |
| iNaturalist Longitude | iNatLongitude | Double |
| iNaturalist Latitude | iNatLatitude | Double |
| Image URLs | ImageURLs | String(512) |
| Image Attribution | ImageAttribution | String(256) |
| Location Accuracy | LocationAccuracy | Integer |

### Visits_Table

| Display Name | Internal Name | Type |
|-------------|--------------|------|
| Date Visit Made | DateCheck | Date |
| Area m2 | Area | Double |
| Height | Height | Double |
| Treated | Treated | String(255) |
| How treated | HowTreated | String(255) |
| Treatment substance | TreatmentSubstance | String(80) |
| Treatment details | TreatmentDetails | String(256) |
| Plant phenology | Flowering | String(255) |
| Radius (m) of area surveyed | CheckedNearbyRadius | Double |
| description | Notes | String(3000) |
| Date for next visit | DateForReturnVisit | Date |
| id | iNatRef | String(72) |
| url | iNaturalistURL | String(256) |
| Site difficulty | SiteDifficulty | String(256) |
| ObservationQuality | ObservationQuality | String(256) |
| WeedVisitStatus | WeedVisitStatus | String(80) |
| RecordedByUserId | RecordedByUserId | String(64) |
| RecordedByUserName | RecordedByUserName | String(64) |
| RecordedDate | RecordedDate | Date |

## Configuration Files

- **taxon_mapping.json**: Maps iNaturalist taxon IDs to CAMS species codes
- **cams_schema.json**: Defines CAMS field names, types, and value mappings
- **sync_configuration.json**: Defines which iNaturalist projects/taxa to sync

## Implementation Files

- **inaturalist_reader.py**: Reads and flattens iNaturalist observations
- **translator.py**: Transforms iNaturalist observations to CAMS features
- **cams_writer.py**: Writes CAMS features to ArcGIS
- **inaturalist_observation.py**: Defines the intermediate iNatObservation structure
- **cams_feature.py**: Defines the CAMS feature structure (WeedLocation, WeedVisit)

