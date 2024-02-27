#  ====================================================================
#  Copyright 2023 EcoNet.NZ
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#  ====================================================================

Feature: Processing an updated iNaturalist observation populates the existing WeedLocation feature correctly

	Rule: Changes to irrelevant fields are ignored
		Example: The observation is verified by another user
		Given iNaturalist has an existing OMB observation which has been synced
		And the OMB observation is verified by another user
		When we process the observation
	    Then the WeedLocations feature has an associated record with 1 child visits record
		And the existing OMB observation is unchanged

		Example: An observation with multiple visit records is verified by another user
	      Given iNaturalist has a new OMB observation with 'observed_on' = 2 years ago
	      And that observation has been synced
		  And 'Date of status update' is updated to yesterday
	      And 'Status update' is updated to 'Dead / Not Present'
		  And that observation has been synced
		  And we read the updated observation
		  And the OMB observation is verified by another user
		  When we process the observation
		  Then the updated observation is unchanged
	      And  the WeedLocations feature has an associated record with 2 child visits record

    Rule: The weed geolocation is updated when changed
        Example: The geolocation is updated
        Given iNaturalist has an existing OMB observation at 'latitude': -41.2920665997, 'longitude': 174.7628175
        And that observation has been synced
        And the geolocation is updated to 'latitude': -41.1234567, 'longitude': 174.7654321
        When we process the observation
        Then a WeedLocations feature is set to geopoint 'x': 19454798.909638427, 'y': -5030568.588554074 in coordinate system EPSG:3857

	Rule: The weed location record is updated with changes to relevant fields
		Example: The location info is updated
		Given iNaturalist has an existing OMB observation which has been synced
		And the 'Location details' are updated to 'Flat 7, 321A St Kilda Road'
		When we process the observation
		Then the feature has 'LocationInfo' set to 'Flat 7, 321A St Kilda Road'

	Rule: The weed visit record is updated with changes to relevant fields
		Example: The Observation Quality is updated
		Given iNaturalist has an existing OMB observation which has been synced
		And the quality grade is updated to 'research'
		When we process the observation
		Then the visits table has 1 records for this observation
		And the visits record has 'ObservationQuality' set to 'research_grade'

