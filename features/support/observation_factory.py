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

from factory import Factory, Sequence
import pyinaturalist


class ObservationFactory(Factory):
    class Meta:
        model = pyinaturalist.Observation

    id = Sequence(lambda n: 2000 + n)
    taxon = pyinaturalist.Taxon()
    taxon.id = 160697
    taxon.ancestor_ids = [160697]
    observed_on = '2022-10-21T12:34:56+12:00'
    location = Sequence(lambda n: (-41.371254 - n * 0.01, 174.593524))
    user = pyinaturalist.User()
    user.id = 999999
    created_at = '2022-10-22T13:45:56'
    quality_grade = 'casual'
    description = None
