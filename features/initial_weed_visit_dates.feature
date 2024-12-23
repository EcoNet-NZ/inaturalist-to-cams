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

Feature: DateVisitMade (DateCheck) and Follow-up dates are set correctly

	Rule:
		DateVisitMade is set to the latest of 'Date controlled' or 'Date of status update'.
		If neither of these are set, DateVisitMade is set to the 'Observed at' date.

		Example: New observation without weed being controlled or status update
		Given iNaturalist has a new OMB observation observed at 2022-11-09T12:23:34+12:00 with no date controlled and no date of status update
		When we process the observation
		Then the visits record has date 'DateCheck' set to '2022-11-09 12:23:34'

		Example: New observation with controlled date
		Given iNaturalist has a new OMB observation observed at 2022-11-09T12:23:34+12:00 with date controlled of 2022-11-11T19:33:44+12:00 and no date of status update
		When we process the observation
		Then the visits record has date 'DateCheck' set to '2022-11-11 19:33:44'

		Example: New observation with status update date
		Given iNaturalist has a new OMB observation observed at 2022-11-09T12:23:34+12:00 with no date controlled and date of status update of 2022-11-15T19:10:11+12:00
		When we process the observation
		Then the visits record has date 'DateCheck' set to '2022-11-15 19:10:11'

		Example: New observation with status update date after controlled date
		Given iNaturalist has a new OMB observation observed at 2022-11-09T12:23:34+12:00 with date controlled of 2022-11-11T19:33:44+12:00 and date of status update of 2022-11-12T09:10:11+12:00
		When we process the observation
		Then the visits record has date 'DateCheck' set to '2022-11-12 09:10:11'

		Example: New observation with status update date before controlled date
		Given iNaturalist has a new OMB observation observed at 2022-11-09T12:23:34+12:00 with date controlled of 2022-12-22T19:33:44+12:00 and date of status update of 2022-11-12T09:10:11+12:00
		When we process the observation
		Then the visits record has date 'DateCheck' set to '2022-12-22 19:33:44'

	Rule:
		If Follow-up date in iNaturalist is not set, the Follow-up field on the CAMS visit record is left blank

		@wip
		Example: New observation with Follow-up date left blank
		Given iNaturalist has a new OMB observation
		When we process the observation
		Then the visits record has 'DateForReturnVisit' set to None

	Rule:

		@wip
		Example: Follow-up date is 2025-02-14
		Given iNaturalist has a new OMB observation with 'Follow-up date' set to '2025-02-14'
		When we process the observation
		Then the visits record has date 'DateForReturnVisit' set to '2025-02-14'
