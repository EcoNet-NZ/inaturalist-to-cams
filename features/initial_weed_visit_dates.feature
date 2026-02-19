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

Feature: DateVisitMade (DateCheck) and 'Date for next visit' (DateForReturnVisit) are set correctly

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
		If 'Date for next visit' in iNaturalist is not set, the 'Date for next visit' field on the CAMS visit record is left blank

		Example: New observation with 'Date for next visit' left blank
		Given iNaturalist has a new OMB observation
		When we process the observation
		Then the visits record has 'DateForReturnVisit' set to None

	Rule:
		The 'Date for next visit' observation field value is used for DateForReturnVisit

		Example: 'Date for next visit' is 2025-02-14
		Given iNaturalist has a new OMB observation with date 'Date for next visit' set to '2025-02-14'
		When we process the observation
		Then the visits record has date 'DateForReturnVisit' set to '2025-02-14'

	Rule:
		Legacy field. If the 'Date for next visit' observation field is blank, the 'Follow-up (YYYY-MM)' observation field value is used for DateForReturnVisit.
		This field refers to the first day of the specified month.

		Example: 'Follow-up (YYYY-MM)' set to '2022-12'
		Given iNaturalist has a new OMB observation with 'Follow-up (YYYY-MM)' set to '2022-12'
		When we process the observation
		Then the visits record has date 'DateForReturnVisit' set to '2022-12-01'

	Rule:
		If both 'Date for next visit' and 'Follow-up (YYYY-MM)' are set, the 'Date for next visit' observation field value is used for DateForReturnVisit

		Example: 'Date for next visit' is 2025-07-17 and Follow-up (YYYY-MM)' set to '2023-01'
		Given iNaturalist has a new OMB observation with date 'Date for next visit' set to '2025-02-14'
		And 'Follow-up (YYYY-MM)' is set to '2023-01'
		When we process the observation
		Then the visits record has date 'DateForReturnVisit' set to '2025-02-14'

	Rule:
		If 'Date for next visit' is before or on the visit date, DateForReturnVisit is left blank

		Example: 'Date for next visit' is before visit date
		Given iNaturalist has a new OMB observation observed at 2025-03-15T12:00:00+12:00
		And 'Date for next visit' is set to '2025-03-10'
		When we process the observation
		Then the visits record has 'DateForReturnVisit' set to None

		Example: 'Date for next visit' is same as visit date
		Given iNaturalist has a new OMB observation observed at 2025-03-15T12:00:00+12:00
		And 'Date for next visit' is set to '2025-03-15'
		When we process the observation
		Then the visits record has 'DateForReturnVisit' set to None

		Example: 'Date for next visit' is after visit date
		Given iNaturalist has a new OMB observation observed at 2025-03-15T12:00:00+12:00
		And 'Date for next visit' is set to '2025-03-20'
		When we process the observation
		Then the visits record has date 'DateForReturnVisit' set to '2025-03-20'

		