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

Feature: Processing a new iNaturalist observation does not cause an invalid HTML error

	Rule: Google Map references are removed from html links
		Example: A google map reference is replaced
		Given iNaturalist has a new OMB observation with description set to 'Map Link <a href="https://www.google.co.nz/maps/@-36.870013,174.8628706,3a,21.3y,172.22h,83.33t/data=!3m6!1e1!3m4!1sWNeFx4TNIV6kKLgalvaGuA!2e0!7i13312!8i6656!6m1!1e1">Street View - Nov 2015</a>'
		When we process the observation
		Then the visits record has 'NotesAndDetails' set to 'Map Link <a href="">Street View - Nov 2015</a>'

#Original problem message: '<em>Locality: NEW ZEALAND AK, suburb of Glen Innes, Paddington Reserve (W Tamaki Rd entrance).\r\n\r\n<em>Habitat: One large plant, 3-4 m high. The plant is visible on 
#<a href="https://www.google.co.nz/maps/@-36.870013,174.8628706,3a,21.3y,172.22h,83.33t/data=!3m6!1e1!3m4!1sWNeFx4TNIV6kKLgalvaGuA!2e0!7i13312!8i6656!6m1!1e1">Street View - Nov 2015</a>
		