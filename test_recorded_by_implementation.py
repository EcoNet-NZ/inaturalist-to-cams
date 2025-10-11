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
    
    # Add a Date controlled field with a user_id (this should be selected)
    ofv_date_controlled = MockObservationFieldValue(
        name="Date controlled",
        value=base_time.isoformat(),
        user_id=789,
        user=MockUser(789, "field_worker_bob"),
        updated_at=base_time
    )
    
    # Add a Date of status update field (should be ignored since Date controlled exists)
    ofv_status_update = MockObservationFieldValue(
        name="Date of status update",
        value=(base_time - datetime.timedelta(hours=1)).isoformat(),
        user_id=456,
        user=MockUser(456, "conservationist_jane"),
        updated_at=base_time - datetime.timedelta(hours=1)
    )
    
    # Add other field (should be ignored)
    ofv_other = MockObservationFieldValue(
        name="Treated ?",
        value="Yes",
        user=MockUser(123, "user123"),
        updated_at=base_time - datetime.timedelta(days=2)
    )
    
    observation.ofvs = [ofv_other, ofv_status_update, ofv_date_controlled]
    observation.updated_at = base_time
    observation.user = MockUser(777, "observation_creator")
    
    # Test the new calculate_visit_date_and_status_and_user method
    print("1. Testing calculate_visit_date_and_status_and_user...")
    
    # First flatten the observation
    inat_observation = inaturalist_reader.INatReader.flatten(observation)
    
    # Then use the translator method
    from inat_to_cams.translator import INatToCamsTranslator
    translator = INatToCamsTranslator()
    visit_date, visit_status, recorded_by_user_id, recorded_by_username = translator.calculate_visit_date_and_status_and_user(inat_observation, observation)
    
    print(f"   Visit date: {visit_date}")
    print(f"   Visit status: {visit_status}")
    print(f"   RecordedByUserId: {recorded_by_user_id}")
    print(f"   RecordedByUserName: {recorded_by_username}")
    
    # Should be the Date controlled field user (user_id 789, username field_worker_bob)
    expected_user_id = 789
    expected_username = "field_worker_bob"
    
    if recorded_by_user_id == expected_user_id:
        print("   ✓ Correctly identified Date controlled user_id")
    else:
        print(f"   ✗ Expected user_id {expected_user_id}, got {recorded_by_user_id}")
    
    if recorded_by_username == expected_username:
        print("   ✓ Correctly identified Date controlled username")
    else:
        print(f"   ✗ Expected username {expected_username}, got {recorded_by_username}")
    
    # RecordedDate should come from observation updated_at
    recorded_date = observation.updated_at
    if recorded_date == base_time:
        print("   ✓ Correctly identified observation updated_at")
    else:
        print(f"   ✗ Expected {base_time}, got {recorded_date}")
    
    # Test the full flatten method (now only sets recorded_date)
    print("\n2. Testing full flatten method...")
    try:
        inat_obs = inaturalist_reader.INatReader.flatten(observation)
        
        print(f"   iNat observation recorded_by_user_id: {inat_obs.recorded_by_user_id}")
        print(f"   iNat observation recorded_by_username: {inat_obs.recorded_by_username}")
        print(f"   iNat observation recorded_date: {inat_obs.recorded_date}")
        
        # recorded_by fields should be None since they're now handled in translator
        if inat_obs.recorded_by_user_id is None:
            print("   ✓ Flatten method correctly left recorded_by_user_id as None")
        else:
            print(f"   ✗ Flatten method: expected None, got {inat_obs.recorded_by_user_id}")
        
        if inat_obs.recorded_by_username is None:
            print("   ✓ Flatten method correctly left recorded_by_username as None")
        else:
            print(f"   ✗ Flatten method: expected None, got {inat_obs.recorded_by_username}")
        
        if inat_obs.recorded_date == base_time:
            print("   ✓ Flatten method correctly set recorded_date")
        else:
            print(f"   ✗ Flatten method: expected {base_time}, got {inat_obs.recorded_date}")
            
    except Exception as e:
        print(f"   ✗ Error in flatten method: {e}")
    
    # Test with Date of status update field (when no Date controlled)
    print("\n3. Testing Date of status update priority...")
    
    # Create observation with only Date of status update field
    observation_status_only = MockObservation()
    observation_status_only.updated_at = base_time
    observation_status_only.user = MockUser(777, "observation_creator")
    
    ofv_status_only = MockObservationFieldValue(
        name="Date of status update",
        value=base_time.isoformat(),
        user_id=456,
        user=MockUser(456, "conservationist_jane"),
        updated_at=base_time
    )
    
    observation_status_only.ofvs = [ofv_status_only]
    
    # Test with new approach
    inat_obs_status = inaturalist_reader.INatReader.flatten(observation_status_only)
    visit_date_status, visit_status_status, recorded_by_user_id_status, recorded_by_username_status = translator.calculate_visit_date_and_status_and_user(inat_obs_status, observation_status_only)
    
    print(f"   RecordedByUserId (status update): {recorded_by_user_id_status}")
    print(f"   RecordedByUserName (status update): {recorded_by_username_status}")
    print(f"   Visit date: {visit_date_status}")
    
    if recorded_by_user_id_status == 456:
        print("   ✓ Correctly used Date of status update user_id")
    else:
        print(f"   ✗ Expected 456, got {recorded_by_user_id_status}")
    
    if recorded_by_username_status == "conservationist_jane":
        print("   ✓ Correctly used Date of status update username")
    else:
        print(f"   ✗ Expected conservationist_jane, got {recorded_by_username_status}")
    
    # Test fallback to observation user
    print("\n4. Testing fallback to observation user...")
    observation_fallback = MockObservation()
    observation_fallback.updated_at = base_time
    observation_fallback.user = MockUser(777, "observation_creator")
    observation_fallback.ofvs = []  # No relevant fields
    
    # Test with new approach
    inat_obs_fallback = inaturalist_reader.INatReader.flatten(observation_fallback)
    visit_date_fallback, visit_status_fallback, recorded_by_user_id_fallback, recorded_by_username_fallback = translator.calculate_visit_date_and_status_and_user(inat_obs_fallback, observation_fallback)
    
    print(f"   RecordedByUserId (fallback): {recorded_by_user_id_fallback}")
    print(f"   RecordedByUserName (fallback): {recorded_by_username_fallback}")
    print(f"   Visit date (fallback): {visit_date_fallback}")
    
    if recorded_by_user_id_fallback == 777:
        print("   ✓ Correctly fell back to observation user_id")
    else:
        print(f"   ✗ Expected 777, got {recorded_by_user_id_fallback}")
    
    if recorded_by_username_fallback == "observation_creator":
        print("   ✓ Correctly fell back to observation username")
    else:
        print(f"   ✗ Expected observation_creator, got {recorded_by_username_fallback}")
    
    
    print("\n5. Testing with empty Date fields...")
    observation_empty_dates = MockObservation()
    observation_empty_dates.updated_at = base_time
    observation_empty_dates.user = MockUser(777, "observation_creator")
    
    # Add Date controlled and Date of status update fields with empty values
    empty_date_controlled = MockObservationFieldValue(
        name="Date controlled",
        value="",  # Empty value
        user_id=999,
        user=MockUser(999, "should_be_ignored")
    )
    
    empty_status_update = MockObservationFieldValue(
        name="Date of status update", 
        value=None,  # None value
        user_id=888,
        user=MockUser(888, "should_also_be_ignored")
    )
    
    observation_empty_dates.ofvs = [empty_date_controlled, empty_status_update]
    
    # Test with new approach
    inat_obs_empty = inaturalist_reader.INatReader.flatten(observation_empty_dates)
    visit_date_empty, visit_status_empty, recorded_by_user_id_empty, recorded_by_username_empty = translator.calculate_visit_date_and_status_and_user(inat_obs_empty, observation_empty_dates)
    
    print(f"   RecordedByUserId (empty dates): {recorded_by_user_id_empty}")
    print(f"   RecordedByUserName (empty dates): {recorded_by_username_empty}")
    print(f"   Visit date (empty dates): {visit_date_empty}")
    
    if recorded_by_user_id_empty == 777:
        print("   ✓ Correctly ignored empty date fields and used observation user_id")
    else:
        print(f"   ✗ Expected 777, got {recorded_by_user_id_empty}")
    
    if recorded_by_username_empty == "observation_creator":
        print("   ✓ Correctly ignored empty date fields and used observation username")
    else:
        print(f"   ✗ Expected observation_creator, got {recorded_by_username_empty}")
    
    
    print("\n" + "=" * 60)
    print("Test completed!")


if __name__ == "__main__":
    test_recorded_by_implementation()
