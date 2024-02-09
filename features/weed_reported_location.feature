
Feature: Processing iNaturalist observations populates the reported weed location correctly

    Rule: The reported location fields are at the correct latitude and longitude
        Example: Correct reported location is set for new observations
            Given iNaturalist has a new OMB observation at 'latitude': -41.2920665997, 'longitude': 174.7628175
            When we process the observation
            Then the reported location is recorded as 'latitude': -41.2920665997, 'longitude': 174.7628175
    
 
    Rule: The weed reported location is updated when geolocation is changed
        Example: The reported location is updated when the geolocation is changed
        Given iNaturalist has an existing OMB observation at 'latitude': -41.2920665997, 'longitude': 174.7628175
        And that observation has been synced
        And the geolocation is updated to 'latitude': -41.1234567, 'longitude': 174.7654321
        When we process the observation
        Then the reported location is recorded as 'latitude': -41.1234567, 'longitude': 174.7654321
       
    Rule: Existing iNat observations whose geolocation matches the CAMS reported-location do not overwrite the CAMS geolocation when other details have changed
        Example: The CAMS geolocation is not updated if the CAMS reported-location is the same as the inat-observation location       
        Given iNaturalist has an existing OMB observation at 'latitude': -41.2920665997, 'longitude': 174.7628175
        And that observation has been synced
        And 'Date controlled' is updated to yesterday
        And the CAMS weedlocation is changed to 'latitude': -41.2920665999, 'longitude': 174.7628999
        When we process the observation       
		Then the CAMS weedlocation remains set to 'latitude': -41.2920665999, 'longitude': 174.7628999