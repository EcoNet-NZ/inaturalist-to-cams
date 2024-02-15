#  ====================================================================
#  Copyright 2024 EcoNet.NZ
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

Feature: Processing iNaturalist observations populates the reported weed location correctly

    Rule: The reported location fields are at the correct latitude and longitude
        Example: Correct reported location is set for new observations
            Given iNaturalist has a new OMB observation at 'latitude': -41.2920665997, 'longitude': 174.7628175
            When we process the observation
            Then the reported location is recorded as 'latitude': -41.2920665997, 'longitude': 174.7628175
    
 
    Rule: The CAMS reported location is updated when the iNaturalist observation geolocation is changed
        Example: The CAMS reported location is updated when the iNaturalist geolocation is changed
            Given iNaturalist has an existing OMB observation at 'latitude': -41.2920665997, 'longitude': 174.7628175
            And that observation has been synced
            And the geolocation is updated to 'latitude': -41.1234567, 'longitude': 174.7654321
            When we process the observation
            Then the reported location is recorded as 'latitude': -41.1234567, 'longitude': 174.7654321
       
    Rule: Existing iNat observations whose geolocation matches the CAMS reported-location do not overwrite the CAMS geolocation when other details have changed
        Example: The CAMS geolocation is not updated if the CAMS reported-location is the same as the inat-observation location       
            Given iNaturalist has an existing OMB observation at 'latitude': -41.123456, 'longitude': 174.123456
            And that observation has been synced
            And the CAMS weedlocation has been manually updated to 'latitude': -41.123666, 'longitude': 174.123666
            And the iNaturalist 'Date controlled' is updated 
            When we process the observation       
            Then the CAMS weedlocation remains set to 'latitude': -41.123666, 'longitude': 174.123666

    Rule: Both the CAMS geolocation and the CAMS reported-location are updated when the iNaturalist geolocation is changed
        Example: For an unchanged CAMS feature, the CAMS geolocation and reported-location are updated when the original iNaturalist geolocation is changed
            Given iNaturalist has an existing OMB observation at 'latitude': -41.291111, 'longitude': 174.761111
            And that observation has been synced
            And the geolocation is updated to 'latitude': -41.292222, 'longitude': 174.762222
            When we process the observation
            Then the reported location is recorded as 'latitude': -41.292222, 'longitude': 174.762222
            And the CAMS weedlocation is set to 'latitude': -41.292222, 'longitude': 174.762222

        Example: For a changed CAMS feature, the CAMS geolocation and reported-location are updated when the iNaturalist geolocation is changed
            Given iNaturalist has an existing OMB observation at 'latitude': -41.291111, 'longitude': 174.761111
            And that observation has been synced
            And the CAMS weedlocation has been manually updated to 'latitude': -41.123666, 'longitude': 174.123666
            And the geolocation is updated to 'latitude': -41.292222, 'longitude': 174.762222
            When we process the observation
            Then the reported location is recorded as 'latitude': -41.292222, 'longitude': 174.762222
            And the CAMS weedlocation is set to 'latitude': -41.292222, 'longitude': 174.762222
