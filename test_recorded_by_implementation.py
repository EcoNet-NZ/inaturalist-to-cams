#!/usr/bin/env python
"""
Test script to verify the RecordedBy and RecordedDate implementation.

This script creates a mock observation with observation field values and tests
that the new fields are properly extracted and processed.
"""

import datetime
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from inat_to_cams import inaturalist_observation, inaturalist_reader
from inat_to_cams.username_cache import get_username_cache


class MockUser:
    def __init__(self, user_id, login):
        self.id = user_id
        self.login = login


class MockObservationFieldValue:
    def __init__(self, name, value, user_id=None, user=None, updated_at=None):
        self.name = name
        self.value = value
        self.user_id = user_id
        self.user = user
        self.updated_at = updated_at or datetime.datetime.now()


class MockObservation:
    def __init__(self):
        self.id = 12345
        self.location = [174.593524, -41.371254]  # [longitude, latitude]
        self.positional_accuracy = 10
        self.observed_on = datetime.datetime.now()
        self.created_at = datetime.datetime.now()
        self.taxon = MockTaxon()
        self.description = "Test observation"
        self.quality_grade = "research"
        self.photos = []
        self.ofvs = []


class MockTaxon:
    def __init__(self):
        self.id = 160697
        self.ancestor_ids = [160697]
        self.name = "Test species"
        self.preferred_common_name = "Test plant"


def test_field_registry_completeness():
    """Test that all observation fields used in the code are in the tracked registry"""
    
    print("Testing field registry completeness...")
    print("-" * 40)
    
    # Test the validation method
    is_complete, missing_fields, extra_fields = inaturalist_reader.INatReader.validate_tracked_fields()
    
    if missing_fields:
        print(f"❌ Missing fields in TRACKED_OBSERVATION_FIELDS: {missing_fields}")
    if extra_fields:
        print(f"⚠️  Extra fields in TRACKED_OBSERVATION_FIELDS: {extra_fields}")
    if is_complete and not extra_fields:
        print("✅ All observation fields are properly tracked")
    
    return is_complete


def test_recorded_by_implementation():
    """Test the RecordedBy and RecordedDate implementation"""
    
    print("Testing RecordedBy and RecordedDate implementation...")
    print("=" * 60)
    
    # First test field registry completeness
    print("0. Testing field registry completeness...")
    field_test_passed = test_field_registry_completeness()
    if not field_test_passed:
        print("   ⚠️  Field registry has issues but continuing with other tests...")
    print()
    
    # Create a mock observation with observation field values
    observation = MockObservation()
    
    # Add some observation field values with different timestamps
    base_time = datetime.datetime.now()
    
    # Older field update
    ofv1 = MockObservationFieldValue(
        name="Treated ?",
        value="Yes",
        user=MockUser(123, "user123"),
        updated_at=base_time - datetime.timedelta(days=2)
    )
    
    # More recent field update (this should be the one selected)
    ofv2 = MockObservationFieldValue(
        name="Status update",
        value="Dead / Not Present",
        user=MockUser(456, "conservationist_jane"),
        updated_at=base_time - datetime.timedelta(hours=1)
    )
    
    # Even more recent field update
    ofv3 = MockObservationFieldValue(
        name="Date controlled",
        value=base_time.isoformat(),
        user=MockUser(789, "field_worker_bob"),
        updated_at=base_time
    )
    
    observation.ofvs = [ofv1, ofv2, ofv3]
    
    # Test the get_most_recent_field_update_info method
    print("1. Testing get_most_recent_field_update_info...")
    recorded_by, recorded_date = inaturalist_reader.INatReader.get_most_recent_field_update_info(observation)
    
    print(f"   Most recent update by: {recorded_by}")
    print(f"   Most recent update date: {recorded_date}")
    
    # Should be the most recent one (ofv3)
    expected_user = "field_worker_bob"
    if recorded_by == expected_user:
        print("   ✓ Correctly identified most recent user")
    else:
        print(f"   ✗ Expected {expected_user}, got {recorded_by}")
    
    if recorded_date == base_time:
        print("   ✓ Correctly identified most recent date")
    else:
        print(f"   ✗ Expected {base_time}, got {recorded_date}")
    
    # Test the full flatten method
    print("\n2. Testing full flatten method...")
    try:
        inat_obs = inaturalist_reader.INatReader.flatten(observation)
        
        print(f"   iNat observation recorded_by: {inat_obs.recorded_by}")
        print(f"   iNat observation recorded_date: {inat_obs.recorded_date}")
        
        if inat_obs.recorded_by == expected_user:
            print("   ✓ Flatten method correctly set recorded_by")
        else:
            print(f"   ✗ Flatten method: expected {expected_user}, got {inat_obs.recorded_by}")
        
        if inat_obs.recorded_date == base_time:
            print("   ✓ Flatten method correctly set recorded_date")
        else:
            print(f"   ✗ Flatten method: expected {base_time}, got {inat_obs.recorded_date}")
            
    except Exception as e:
        print(f"   ✗ Error in flatten method: {e}")
    
    # Test username cache
    print("\n3. Testing username cache...")
    cache = get_username_cache()
    stats = cache.get_cache_stats()
    print(f"   Cache stats: {stats}")
    
    # Test with user_id only (no user object)
    print("\n4. Testing with user_id only (cache fallback)...")
    
    # Create observation field value with only user_id
    ofv_with_id = MockObservationFieldValue(
        name="Test field",
        value="Test value",
        user_id=999,
        updated_at=base_time + datetime.timedelta(minutes=1)
    )
    
    observation.ofvs = [ofv_with_id]
    
    recorded_by_cached, recorded_date_cached = inaturalist_reader.INatReader.get_most_recent_field_update_info(observation)
    print(f"   Recorded by (from cache): {recorded_by_cached}")
    print(f"   Recorded date (from cache): {recorded_date_cached}")
    
    # Test empty observation field values
    print("\n5. Testing with no observation field values...")
    observation.ofvs = []
    
    recorded_by_empty, recorded_date_empty = inaturalist_reader.INatReader.get_most_recent_field_update_info(observation)
    print(f"   Recorded by (empty): {recorded_by_empty}")
    print(f"   Recorded date (empty): {recorded_date_empty}")
    
    if recorded_by_empty is None and recorded_date_empty is None:
        print("   ✓ Correctly handled empty observation field values")
    else:
        print("   ✗ Should return None for both values when no OFVs present")
    
    # Test field filtering (only tracked fields should be considered)
    print("\n6. Testing field filtering (only tracked fields)...")
    
    # Add a non-tracked field that's more recent than tracked fields
    non_tracked_ofv = MockObservationFieldValue(
        name="Some Random Field Not In Our System",
        value="Random value",
        user=MockUser(999, "random_user"),
        updated_at=base_time + datetime.timedelta(hours=2)  # Most recent
    )
    
    # Add a tracked field that's older
    tracked_ofv = MockObservationFieldValue(
        name="Treated ?",  # This is in TRACKED_OBSERVATION_FIELDS
        value="Yes",
        user=MockUser(888, "tracked_user"),
        updated_at=base_time + datetime.timedelta(hours=1)  # Less recent
    )
    
    observation.ofvs = [non_tracked_ofv, tracked_ofv]
    
    recorded_by_filtered, recorded_date_filtered = inaturalist_reader.INatReader.get_most_recent_field_update_info(observation)
    print(f"   Most recent (filtered): {recorded_by_filtered} at {recorded_date_filtered}")
    
    # Should use the tracked field, not the non-tracked one
    if recorded_by_filtered == "tracked_user":
        print("   ✅ Correctly filtered to tracked fields only")
    else:
        print(f"   ✗ Expected tracked_user, got {recorded_by_filtered}")
    
    # Test fallback to observation creator/editor
    print("\n7. Testing fallback to observation creator/editor...")
    
    # Create observation with no tracked fields but with user info
    observation_no_fields = MockObservation()
    observation_no_fields.ofvs = [non_tracked_ofv]  # Only non-tracked field
    observation_no_fields.user = MockUser(777, "observation_creator")
    observation_no_fields.created_at = base_time - datetime.timedelta(days=1)
    observation_no_fields.updated_at = base_time - datetime.timedelta(hours=2)
    
    recorded_by_fallback, recorded_date_fallback = inaturalist_reader.INatReader.get_most_recent_field_update_info(observation_no_fields)
    print(f"   Fallback result: {recorded_by_fallback} at {recorded_date_fallback}")
    
    # Should use observation editor (updated_at) first, then creator (created_at)
    if recorded_by_fallback == "observation_creator":
        print("   ✅ Correctly used fallback to observation creator/editor")
    else:
        print(f"   ✗ Expected observation_creator, got {recorded_by_fallback}")
    
    print("\n" + "=" * 60)
    print("Test completed!")


if __name__ == "__main__":
    test_recorded_by_implementation()
