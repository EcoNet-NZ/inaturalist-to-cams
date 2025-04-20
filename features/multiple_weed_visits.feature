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

Feature: Set Visit status for records with multiple visits (WeedVisitStatus)

  	Rule: Controlling a weed patch or updating status after the initial observation creates a 2nd visit

	   Example: New observation with Date Controlled after Date Observed creates 2 visit records
	      Given iNaturalist has a new OMB observation with 'observed_on' = yesterday
	      And that observation has been synced
		  And 'Date controlled' is updated to today
	      And 'Treated ?' is updated to 'Yes'
		  When we process the observation
	      Then the WeedLocations feature has an associated record with 2 child visits record
	      And the first visits record has date 'DateCheck' set to yesterday
	      And the first visits record has 'WeedVisitStatus' set to 'RedGrowth'
	      And the second visits record has date 'DateCheck' set to today
	      And the second visits record has 'WeedVisitStatus' set to 'YellowKilledThisYear'
	      And the feature has 'ParentStatusWithDomain' set to 'YellowKilledThisYear'

	   Example: New observation with Date of Status Update after Date Observed creates 2 visit records
	      Given iNaturalist has a new OMB observation with 'observed_on' = yesterday
	      And that observation has been synced
		  And 'Date of status update' is updated to today
		  And 'Status update' is updated to 'Alive / Regrowth'
		  When we process the observation
	      Then the WeedLocations feature has an associated record with 2 child visits record
	      And the first visits record has date 'DateCheck' set to yesterday
	      And the first visits record has 'WeedVisitStatus' set to 'RedGrowth'
	      And the second visits record has date 'DateCheck' set to today
	      And the second visits record has 'WeedVisitStatus' set to 'RedGrowth'
	      And the feature has 'ParentStatusWithDomain' set to 'RedGrowth'

	   Example: New observation with Date of Status Update after Date Controlled After Date Observed creates 3 visit records
	      Given iNaturalist has a new OMB observation with 'observed_on' = 2 years ago
	      And that observation has been synced

		  And 'Date controlled' is updated to yesterday
	      And 'Treated ?' is updated to 'Yes'
		  And that observation has been synced

		  And 'Date of status update' is updated to today
	      And 'Status update' is updated to 'Dead / Not Present'

		  When we process the observation
	      Then the WeedLocations feature has an associated record with 3 child visits record
	      And the first visits record has date 'DateCheck' set to 2 years ago
	      And the first visits record has 'WeedVisitStatus' set to 'RedGrowth'
	      And the second visits record has date 'DateCheck' set to yesterday
	      And the second visits record has 'WeedVisitStatus' set to 'YellowKilledThisYear'
	      And the third visits record has date 'DateCheck' set to today
	      And the third visits record has 'WeedVisitStatus' set to 'GreenNoRegrowthThisYear'
	      And the feature has 'ParentStatusWithDomain' set to 'GreenNoRegrowthThisYear'

	   Example: CAMS visit followed by iNaturalist verification doesn't create a new visit
	      Given iNaturalist has a new OMB observation with 'observed_on' = 2 years ago
	      And that observation has been synced
	      And a new visits record was created in CAMS with status 'YellowKilledThisYear' yesterday
	      And the OMB observation is verified by another user
	      When we process the observation
	      Then the WeedLocations feature has an associated record with 2 child visits record
	      And the first visits record has date 'DateCheck' set to 2 years ago
	      And the first visits record has 'WeedVisitStatus' set to 'RedGrowth'
	      And the second visits record has date 'DateCheck' set to yesterday
	      And the second visits record has 'WeedVisitStatus' set to 'YellowKilledThisYear'
	      And the feature has 'ParentStatusWithDomain' set to 'YellowKilledThisYear'

	   Example: CAMS visit followed by iNaturalist visit does create a new visit
	      Given iNaturalist has a new OMB observation with 'observed_on' = 2 years ago
	      And that observation has been synced
	      And a new visits record was created in CAMS with status 'YellowKilledThisYear' yesterday
  		  And 'Date of status update' is updated to today
	      And 'Status update' is updated to 'Dead / Not Present'
	      When we process the observation
	      Then the WeedLocations feature has an associated record with 3 child visits record
	      And the first visits record has date 'DateCheck' set to 2 years ago
	      And the first visits record has 'WeedVisitStatus' set to 'RedGrowth'
	      And the second visits record has date 'DateCheck' set to yesterday
	      And the second visits record has 'WeedVisitStatus' set to 'YellowKilledThisYear'
	      And the third visits record has date 'DateCheck' set to today
	      And the third visits record has 'WeedVisitStatus' set to 'GreenNoRegrowthThisYear'
	      And the feature has 'ParentStatusWithDomain' set to 'GreenNoRegrowthThisYear'

	   Example: Weed status rollover followed by iNaturalist verification doesn't create a new visit
	      Given iNaturalist has a new OMB observation with 'observed_on' = 2 years ago
	      And that observation has been synced
	      And the weed instance status was rolled over to 'PurpleHistoric' yesterday
	      And the OMB observation is verified by another user
	      When we process the observation
	      Then the WeedLocations feature has an associated record with 1 child visits record
	      And the first visits record has date 'DateCheck' set to 2 years ago
	      And the first visits record has 'WeedVisitStatus' set to 'RedGrowth'
	      And the feature has 'ParentStatusWithDomain' set to 'PurpleHistoric'

	   Example: Weed status rollover followed by iNaturalist visit does create a new visit
	      Given iNaturalist has a new OMB observation with 'observed_on' = 2 years ago
	      And that observation has been synced
	      And the weed instance status was rolled over to 'PurpleHistoric' yesterday
  		  And 'Date of status update' is updated to today
	      And 'Status update' is updated to 'Dead / Not Present'
	      When we process the observation
	      Then the WeedLocations feature has an associated record with 2 child visits record
	      And the first visits record has date 'DateCheck' set to 2 years ago
	      And the first visits record has 'WeedVisitStatus' set to 'RedGrowth'
	      And the second visits record has date 'DateCheck' set to today
	      And the second visits record has 'WeedVisitStatus' set to 'GreenNoRegrowthThisYear'
	      And the feature has 'ParentStatusWithDomain' set to 'GreenNoRegrowthThisYear'
