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

Feature: Processing a new iNaturalist observation populates the correct taxon on the new WeedLocation feature

	Rule: Taxon must exist in the mapping table
		Example: An error is logged if taxon is not in the mapping file
		Given iNaturalist has a new OMB observation with id 1001 for taxon 123456 with ancestors [123456]
		When we process the observation
		Then the error "Skipping observation 1001 since it has unmapped taxon with lineage" is logged

	Rule: Species is populated with the mapped taxon
		Example: Species is mapped correctly for new observations
		Given iNaturalist has a new OMB observation for taxon 160697 with ancestors [160697]
		When we process the observation
		Then a WeedLocations feature is created with species 'OldMansBeard'

	Rule: Where the mapped taxon is a higher taxa, all descendents of that taxa are mapped
		Example: Section Elkea is mapped to BananaPassionfruit
		Given iNaturalist has a new OMB observation for taxon 879226 with ancestors [878751,879226,133169]
		When we process the observation
		Then a WeedLocations feature is created with species 'BananaPassionfruit'

		Example: Passiflora tripartita (a child of Section Elkea) is also mapped to BananaPassionfruit
		Given iNaturalist has a new OMB observation for taxon 133169 with ancestors [878751,879226,133169]
		When we process the observation
		Then a WeedLocations feature is created with species 'BananaPassionfruit'

		Example: Passiflora tripartita (a grandchild of Section Elkea) is also mapped to BananaPassionfruit
		Given iNaturalist has a new OMB observation for taxon 133171 with ancestors [878751,879226,133169,133171]
		When we process the observation
		Then a WeedLocations feature is created with species 'BananaPassionfruit'

