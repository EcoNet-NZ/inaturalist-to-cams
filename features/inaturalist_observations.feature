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

Feature: iNaturalist observation reader

Rule: Existing iNaturalist observations return location correctly
  Example: Observation with location returns location
     Given iNaturalist observation 63790155 has latitude -41.2783479414 and longitude 174.7796900198
      When we read the observation 63790155
      Then the returned Observation has the location set to latitude = -41.2783479414 and longitude = 174.7796900198

  Example: Observation with private location returns location of None
     Given iNaturalist observation 119681430 has a private location
      When we read the observation 119681430
      Then the returned Observation has the location set to None