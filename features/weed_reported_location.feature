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

Feature: Processing iNaturalist observations populates the CAMS iNaturalist weed location correctly

On an initial synchronisation of an iNaturalist observation to CAMS, the location of the iNaturalist observation is saved to 
the CAMS feature geolocation and to the "iNaturalist Latitude" and "iNaturalist Longitude" fields of the feature. 
These latter two fields are referred to as the "iNaturalist location" below.

After synchronising the observation to CAMS, a user may then update the geolocation of the weed feature on the CAMS map. 
If this occurs, we don't want to overwrite the location updated by the CAMS user unless the iNaturalist user subsequently updates the location.
The synchroniser reads the CAMS feature geolocation and compares it to the CAMS iNaturalist location fields to determine 
whether the location has been updated by the user. If it has, the iNaturalist location will not override the CAMS geolocation.

Rule: Whenever the iNaturalist location is updated, both the CAMS feature geolocation and the iNaturalist location fields are updated
    Example: The CAMS iNaturalist location is set to the iNaturalist location for new observations
        Given iNaturalist has a new observation at 'latitude': -41.2920665997, 'longitude': 174.7628175
        When we process the observation
        Then the iNaturalist location is recorded in CAMS as 'latitude': -41.2920665997, 'longitude': 174.7628175

    Example: The CAMS iNaturalist location is updated when the iNaturalist location is changed
        Given iNaturalist has an existing observation at 'latitude': -41.2920665997, 'longitude': 174.7628175
        And that observation has been synced
        And the geolocation is updated to 'latitude': -41.1234567, 'longitude': 174.7654321
        When we process the observation
        Then the iNaturalist location is recorded in CAMS as 'latitude': -41.1234567, 'longitude': 174.7654321
    
    Example: For an unchanged, existing CAMS feature, the CAMS geolocation and iNaturalist location are updated when the original iNaturalist location is changed
        Given iNaturalist has an existing observation at 'latitude': -41.291111, 'longitude': 174.761111
        And that observation has been synced
        And the geolocation is updated to 'latitude': -41.292222, 'longitude': 174.762222
        When we process the observation
        Then the iNaturalist location is recorded in CAMS as 'latitude': -41.292222, 'longitude': 174.762222
        And the CAMS geolocation is set to 'latitude': -41.292222, 'longitude': 174.762222

    Example: For a changed CAMS feature, the CAMS geolocation and iNaturalist location are updated when the iNaturalist location is changed
        Given iNaturalist has an existing observation at 'latitude': -41.291111, 'longitude': 174.761111
        And that observation has been synced
        And the CAMS geolocation has been manually updated to 'latitude': -41.123666, 'longitude': 174.123666
        And the geolocation is updated to 'latitude': -41.292222, 'longitude': 174.762222
        When we process the observation
        Then the iNaturalist location is recorded in CAMS as 'latitude': -41.292222, 'longitude': 174.762222
        And the CAMS geolocation is set to 'latitude': -41.292222, 'longitude': 174.762222

Rule: After the CAMS user updates the geolocation, it is not overwritten unless the iNaturalist location is subsequently updated
    Example: The CAMS geolocation is not updated if the CAMS iNaturalist location is the same as the iNaturalist location       
        Given iNaturalist has an existing observation at 'latitude': -41.123456, 'longitude': 174.123456
        And that observation has been synced
        And the CAMS geolocation has been manually updated to 'latitude': -41.123666, 'longitude': 174.123666
        And the iNaturalist 'Date controlled' is updated 
        When we process the observation       
        Then the CAMS geolocation remains set to 'latitude': -41.123666, 'longitude': 174.123666


        