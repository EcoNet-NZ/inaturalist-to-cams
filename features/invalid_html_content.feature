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

Feature: Processing iNaturalist observations sanitises invalid HTML links

	Rule: Invalid html references are removed with a warning
		Example: A full google map reference is replaced and a warning issued
		Given iNaturalist has a new OMB observation with description set to 'Map Link <a href="https://www.google.co.nz/maps/@-36.870013,174.8628706,3a,21.3y,172.22h,83.33t/data=!3m6!1e1!3m4!1sWNeFx4TNIV6kKLgalvaGuA!2e0!7i13312!8i6656!6m1!1e1">Street View - Nov 2015</a>'
		When we process the observation
		Then the visits record has 'NotesAndDetails' set to 'Map Link (INVALID URL DETECTED - see iNaturalist link for full notes)'

		Example: An '=' in an href url causes an Invalid URL warning
		Given iNaturalist has a new OMB observation with description set to 'Map Link <a href="https://www.otherplace.co.nz/@-aw,wor.d/data=,1!23">Street View - Nov 2015</a>'
		When we process the observation
		Then the visits record has 'NotesAndDetails' set to 'Map Link (INVALID URL DETECTED - see iNaturalist link for full notes)'

		Example: Two URLS with '=' inside link causes Two Invalid URL warnings
		Given iNaturalist has a new OMB observation with description set to 'Link1: <a href="http://www.link1.com/ab=ab">Value1</a> words here. Link2: <a href="http://www.link2.co.uk/aab/f=ab">Value2</a>'
		When we process the observation
		Then the visits record has 'NotesAndDetails' set to 'Link1: (INVALID URL DETECTED - see iNaturalist link for full notes) words here. Link2: (INVALID URL DETECTED - see iNaturalist link for full notes)'

		Example: '=' not inside a link does not cause a warning
		Given iNaturalist has a new OMB observation with description set to '<div>words=morewords</div>'
		When we process the observation
		Then the visits record has 'NotesAndDetails' set to '<div>words=morewords</div>'

		Example: Link with href but no '=' in the url does not cause a warning
		Given iNaturalist has a new OMB observation with description set to '<a href="http://www.madeup.com">words words</a>'
		When we process the observation
		Then the visits record has 'NotesAndDetails' set to '<a href="http://www.madeup.com">words words</a>'