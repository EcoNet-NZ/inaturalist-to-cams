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


def inat_id_for_instance(location, visits):
    """Observation id from a visit reference, or the weed's iNaturalist URL."""
    for visit in visits:
        reference = visit.get('iNatRef')
        if reference is not None and str(reference).strip() != '':
            return str(reference).strip()
    url = location.get('iNatURL') or ''
    marker = '/observations/'
    if marker in url:
        return url.split(marker, 1)[1].strip().strip('/')
    return None


def _same_number(stored, effort):
    if stored is None or stored == '':
        return False
    return int(float(stored)) == effort


def updates_for_instance(location, visits, effort_to_control):
    """Rows whose stored effort differs from the current iNaturalist value."""
    location_updates = []
    if not _same_number(location.get('effort_to_control'), effort_to_control):
        location_updates.append({
            'OBJECTID': location['OBJECTID'],
            'effort_to_control': effort_to_control,
        })
    visit_updates = []
    for visit in visits:
        if not _same_number(visit.get('effort_to_control'), effort_to_control):
            visit_updates.append({
                'OBJECTID': visit['OBJECTID'],
                'effort_to_control': effort_to_control,
            })
    return location_updates, visit_updates


def stored_attributes(update, field_name):
    """ArcGIS update attributes. field_name is the layer column for effort."""
    return {'OBJECTID': update['OBJECTID'], field_name: update['effort_to_control']}
