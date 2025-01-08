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

Feature: Processing a new iNaturalist observation populates a new WeedVisits record correctly

	Rule: WeedVisits record is created for a new observation and linked to the WeedLocations feature
		Example: New observation creates new rows
		Given iNaturalist has a new OMB observation with id of 1100
		And the visits table does not have a record with iNaturalist id 1100
		When we process the observation
		Then the visits table has 1 record with iNaturalist id 1100
		And the visits record has 'iNaturalistURL' set to 'https://www.inaturalist.org/observations/1100'
		And the WeedLocations feature has an associated record with 1 child visits record

	Rule: Observation Quality is set on observation
		Example: Casual
		Given iNaturalist has a new OMB observation with quality_grade casual
		When we process the observation
		Then the visits record has 'ObservationQuality' set to 'casual'

		Example: Needs ID
		Given iNaturalist has a new OMB observation with quality_grade needs_id
		When we process the observation
		Then the visits record has 'ObservationQuality' set to 'needs_id'

		Example: Research Grade
		Given iNaturalist has a new OMB observation with quality_grade research
		When we process the observation
		Then the visits record has 'ObservationQuality' set to 'research_grade'

	Rule: DateVisitMade is set on WeedVisits record
		Example: DateVisitMade is set correctly
		Given iNaturalist has a new OMB observation with id 1003 observed at 2022-04-03T17:01:00+12:00
		And the visits table does not have a record with iNaturalist id 1003
		When we process the observation
		Then the visits table has 1 record with iNaturalist id 1003
		And the visits record has date 'DateCheck' set to '2022-04-03 17:01:00'

	Rule: Optional fields are set on WeedVisits record
		Example: Height is set if provided
		Given iNaturalist has a new OMB observation with 'Height (m)' set to 9
		When we process the observation
		Then the visits record has 'Height' set to 9

		Example: Area is set if provided
		Given iNaturalist has a new OMB observation with 'Area in square meters' set to 150
		When we process the observation
		Then the visits record has 'Area' set to 150

		Example: Area is set to legacy field if provided
		Given iNaturalist has a new OMB observation with 'Adult Area' set to 122
		When we process the observation
		Then the visits record has 'Area' set to 122

		Example: Area is set to different legacy field if provided
		Given iNaturalist has a new OMB observation with 'area of infestation (m2)' set to 33.3
		When we process the observation
		Then the visits record has 'Area' set to 33.3

		Example: New area field is preferred if both are provided
		Given iNaturalist has a new OMB observation with  'Area in square meters' set to 88 and 'Adult Area' set to 99
		When we process the observation
		Then the visits record has 'Area' set to 88

		Example: Radius surveyed is set if provided
		Given iNaturalist has a new OMB observation with 'Radius (m) of area surveyed' set to 17.5
		When we process the observation
		Then the visits record has 'CheckedNearbyRadius' set to 17.5

		Example: Notes are set if provided
		Given iNaturalist has a new OMB observation with description set to 'Weed climbing up Hinau'
		When we process the observation
		Then the visits record has 'NotesAndDetails' set to 'Weed climbing up Hinau'

		Example: Site difficulty is set if provided
		Given iNaturalist has a new OMB observation with 'Site difficulty' set to '1 Easy (for most people)'
		When we process the observation
		Then the visits record has 'SiteDifficulty' set to '1Easy'

		Example: Site difficulty is set to legacy Professional assistance required field if provided
		Given iNaturalist has a new OMB observation with 'Professional assistance required' set to 'yes'
		When we process the observation
		Then the visits record has 'SiteDifficulty' set to '5Professional'

		Example: New Site difficulty field is preferred if both are provided
		Given iNaturalist has a new OMB observation with  'Site difficulty' set to '1 Easy (for most people)' and 'Professional assistance required' set to 'yes'
		When we process the observation
		Then the visits record has 'SiteDifficulty' set to '1Easy'

		Example: Phenology is set if provided
		Given iNaturalist has a new OMB observation with 'Plant phenology->most common flowering/fruiting reproductive stage' set to 'flower buds'
		When we process the observation
		Then the visits record has 'Flowering' set to '2BudsForming'

		Example: Phenology is set to legacy Fruiting field if provided
		Given iNaturalist has a new OMB observation with 'fruiting' set to 'yes'
		When we process the observation
		Then the visits record has 'Flowering' set to '8PodsBursting'

		Example: Phenology is set to legacy Flowering field if provided
		Given iNaturalist has a new OMB observation with 'Flowering' set to 'yes'
		When we process the observation
		Then the visits record has 'Flowering' set to '3FlowersVisible'

		Example: New phenology field is preferred if both are provided
		Given iNaturalist has a new OMB observation with  'Plant phenology->most common flowering/fruiting reproductive stage' set to 'flower buds' and 'Flowering' set to 'yes'
		When we process the observation
		Then the visits record has 'Flowering' set to '2BudsForming'

		Example: Treated is set if provided
		Given iNaturalist has a new OMB observation with 'Treated ?' set to 'Partially'
		When we process the observation
		Then the visits record has 'Treated' set to 'Partially'

		Example: Treated is set to legacy Is the pest controlled? field if provided
		Given iNaturalist has a new OMB observation with 'Is the pest controlled?' set to 'yes'
		When we process the observation
		Then the visits record has 'Treated' set to 'Yes'

		Example: Treated is set to legacy dead field if provided
		Given iNaturalist has a new OMB observation with 'dead or alive?' set to 'dead'
		When we process the observation
		Then the visits record has 'Treated' set to 'Yes'

		Example: New Treated field is preferred if both are provided
		Given iNaturalist has a new OMB observation with  'Treated ?' set to 'Partially' and 'Is the pest controlled?' set to 'yes'
		When we process the observation
		Then the visits record has 'Treated' set to 'Partially'

		Example: How treated is set if provided
		Given iNaturalist has a new OMB observation with 'How treated' set to 'Pulled or dug'
		When we process the observation
		Then the visits record has 'HowTreated' set to 'PulledOrDug'

		Example: Treatment Substance is set if provided
		Given iNaturalist has a new OMB observation with 'Treatment substance' set to 'CutNPaste Glimax'
		When we process the observation
		Then the visits record has 'TreatmentSubstance' set to 'CutNPasteGlimax'

		Example: Treatment Substance is not set if None
		Given iNaturalist has a new OMB observation with 'Treatment substance' set to 'None'
		When we process the observation
		Then the visits record has 'TreatmentSubstance' set to None

		Example: Treatment Details are set if provided
		Given iNaturalist has a new OMB observation with 'Treatment details' set to 'Roots grubbed and herbicide applied'
		When we process the observation
		Then the visits record has 'TreatmentDetails' set to 'Roots grubbed and herbicide applied'

