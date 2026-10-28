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

import unittest

from inat_to_cams.effort import effort_value
from migration.effort_updates import inat_id_for_instance, stored_attributes, updates_for_instance


class EffortValueTests(unittest.TestCase):
    def test_first_digit_is_the_effort(self):
        self.assertEqual(effort_value('3 = Three person hours'), 3)

    def test_blank_effort_defaults_to_one(self):
        self.assertEqual(effort_value(None), 1)
        self.assertEqual(effort_value(''), 1)


class EffortUpdateTests(unittest.TestCase):
    def test_inat_id_comes_from_the_visit_reference(self):
        location = {'iNatURL': 'https://www.inaturalist.org/observations/99'}
        visits = [{'iNatRef': '42'}]
        self.assertEqual(inat_id_for_instance(location, visits), '42')

    def test_inat_id_falls_back_to_the_weed_url(self):
        location = {'iNatURL': 'https://www.inaturalist.org/observations/99'}
        self.assertEqual(inat_id_for_instance(location, []), '99')

    def test_changed_rows_are_the_only_updates(self):
        location = {'OBJECTID': 10, 'effort_to_control': 1}
        visits = [
            {'OBJECTID': 1, 'effort_to_control': 1},
            {'OBJECTID': 2, 'effort_to_control': None},
        ]
        location_updates, visit_updates = updates_for_instance(location, visits, 3)
        self.assertEqual(location_updates, [{'OBJECTID': 10, 'effort_to_control': 3}])
        self.assertEqual(visit_updates, [
            {'OBJECTID': 1, 'effort_to_control': 3},
            {'OBJECTID': 2, 'effort_to_control': 3},
        ])
        self.assertEqual(
            stored_attributes(location_updates[0], 'effort_column'),
            {'OBJECTID': 10, 'effort_column': 3},
        )

    def test_matching_values_are_left_unchanged(self):
        location = {'OBJECTID': 10, 'effort_to_control': 3.0}
        visits = [{'OBJECTID': 1, 'effort_to_control': 3}]
        location_updates, visit_updates = updates_for_instance(location, visits, 3)
        self.assertEqual(location_updates, [])
        self.assertEqual(visit_updates, [])


if __name__ == '__main__':
    unittest.main()
