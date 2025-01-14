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

Feature: GeoPrivacy and LandOwnership are only set on the initial synchronisation

	Rule: The geoprivacy field is set to Open on initial sync (we only sync inat records with geoprivacy='open' currently)
		Example: geoprivacy is set to Open on initial sync
		Given iNaturalist has a new OMB observation
		When we process the observation
		Then the feature has 'GeoPrivacy' set to 'Open'

		Example: geoprivacy stays as Open on subsequent sync
		Given iNaturalist has an existing OMB observation which has been synced
		And the quality grade is updated to 'research'
		When we process the observation
		Then the feature has 'GeoPrivacy' set to 'Open'

	Rule: The geoprivacy field is not overwritten by a subsequent sync
		Example: geoprivacy is set to Private through CAMS and not overwritten by the sync code
		Given iNaturalist has an existing OMB observation which has been synced
		And the CAMS geoprivacy has been updated in CAMS to 'Private'
		And the quality grade is updated to 'research'
		When we process the observation
		Then the feature has 'GeoPrivacy' set to 'Private'

	Rule: The land ownership field is set to Not Available on initial sync
		Example: land ownership is set to Not Available on initial sync
		Given iNaturalist has a new OMB observation
		When we process the observation
		Then the feature has 'LandOwnership' set to 'NotAvailable'

	Rule: The land ownership field is not overwritten by a subsequent sync
		Example: land ownership is set to Council through CAMS and not overwritten by the sync code
		Given iNaturalist has an existing OMB observation which has been synced
		And the CAMS land ownership has been updated in CAMS to 'Council'
		And the quality grade is updated to 'research'
		When we process the observation
		Then the feature has 'LandOwnership' set to 'Council'		