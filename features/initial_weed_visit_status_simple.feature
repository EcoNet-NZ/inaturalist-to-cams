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

Feature: Set Visit status (WeedVisitStatus)

  	Rule:
		* Weeds are rolled over to PURPLE at the start of September, even if controlled or updated before then

      Example: New observation without weed being controlled or status update last year (PURPLE)
         Given iNaturalist has a new OMB observation with DateVisitMade before the previous 1st July
            When we process the observation
            Then the visits record has 'WeedVisitStatus' set to 'PurpleHistoric'

      Example: New observation with weed being controlled last year (PURPLE)
         Given iNaturalist has a new OMB observation with 'Date controlled' before the previous 1st July
            When we process the observation
            Then the visits record has 'WeedVisitStatus' set to 'PurpleHistoric'

      Example: New observation with weed being updated last year (PURPLE)
         Given iNaturalist has a new OMB observation with 'Date of status update' before the previous 1st July
            When we process the observation
            Then the visits record has 'WeedVisitStatus' set to 'PurpleHistoric'         

  	Rule:
      * Any weeds observed in the previous 2 months (ie since start July) are not rolled over
		* By default, observation status is set to RED
  
      Example: New observation without weed being controlled or status update today (RED)
         Given iNaturalist has a new OMB observation with DateVisitMade set to the previous 1st July
            When we process the observation
            Then the visits record has 'WeedVisitStatus' set to 'RedGrowth'

  	Rule:
		* If 'How treated' = 'Cut but roots remain', status is set to ORANGE

      Example: New observation controlled today with 'Cut but roots remain' (ORANGE)
         Given iNaturalist has a new OMB observation with 'Date controlled' = today and 'How treated' = 'Cut but roots remain'
            When we process the observation
            Then the visits record has 'WeedVisitStatus' set to 'OrangeDeadHeaded'

  	Rule:
		* Else if 'Treated ?' = 'Yes', status is set to YELLOW

      Example: New observation controlled today with 'Treated' = 'Yes' (YELLOW)
         Given iNaturalist has a new OMB observation with 'Date controlled' = today and 'Treated ?' = 'Yes'
            When we process the observation
            Then the visits record has 'WeedVisitStatus' set to 'YellowKilledThisYear'

  	Rule:
		* If 'Treated ?' = 'No' or 'Partially', status is set to YELLOW

      Example: New observation controlled today with 'Treated' = 'No' (RED)
         Given iNaturalist has a new OMB observation with 'Date controlled' = today and 'Treated ?' = 'No'
            When we process the observation
            Then the visits record has 'WeedVisitStatus' set to 'RedGrowth'

      Example: New observation controlled today with 'Treated' = 'Partially' (RED)
         Given iNaturalist has a new OMB observation with 'Date controlled' = today and 'Treated ?' = 'Partially'
            When we process the observation
            Then the visits record has 'WeedVisitStatus' set to 'RedGrowth'

  	Rule:
		* Else if the plant is updated that it is alive, set the status to RED

      Example: New observation updated today with Status update = Alive (RED)
         Given iNaturalist has a new OMB observation with 'Date of status update' = today and 'Status update' = 'Alive / Regrowth'
            When we process the observation
            Then the visits record has 'WeedVisitStatus' set to 'RedGrowth'

  	Rule:
		* Else if the plant is updated that it is dead, set the status to GREEN

      Example: New observation updated today with Status update = Dead (GREEN)
         Given iNaturalist has a new OMB observation with 'Date of status update' = today and 'Status update' = 'Dead / Not Present'
            When we process the observation
            Then the visits record has 'WeedVisitStatus' set to 'GreenNoRegrowthThisYear'

  	Rule:
		* Else if the plant is updated that it is a duplicate, set the status to GRAY

      Example: New observation updated today with Status update = Duplicate (GRAY)
         Given iNaturalist has a new OMB observation with 'Date of status update' = today and 'Status update' = 'Duplicate'
            When we process the observation
            Then the visits record has 'WeedVisitStatus' set to 'GrayDuplicate'
