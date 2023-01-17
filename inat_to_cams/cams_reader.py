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

import logging
from datetime import datetime
import pytz

from inat_to_cams import cams_interface, cams_observation, config


class CamsReader:

    def read_observation(self, inat_id):
        query_table = f"iNatRef='{inat_id}'"
        logging.info(f'Reading CAMS feature where {query_table}')
        rows = cams_interface.connection.query_weed_visits_table(query_table)
        if not rows:
            logging.info('No existing observation found')
            return None

        weed_visits = []
        location_guid = None

        logging.info(f'Found existing CAMS feature with {len(rows)} visit rows')

        for row in rows:
            logging.info(f'Found visit table row {row}')
            visit = cams_observation.WeedVisit()
            cams_schema_config = config.cams_schema_config
            visit.object_id = row.attributes['OBJECTID']
            visit.external_id = row.attributes['iNatRef']
            visit.external_url = row.attributes['iNaturalistURL']
            visit.date_visit_made = self.as_datetime(row.attributes['DateCheck'])
            visit.height = row.attributes['Height']
            visit.area = row.attributes['Area']
            visit.radius_surveyed = row.attributes['CheckedNearbyRadius']
            visit.site_difficulty = cams_schema_config.cams_field_key('Visits_Table', 'Site difficulty', row.attributes['SiteDifficulty'])
            visit.follow_up_date = row.attributes['DateForReturnVisit']
            visit.phenology = cams_schema_config.cams_field_key('Visits_Table', 'Plant phenology->most common flowering/fruiting reproductive stage', row.attributes['Flowering'])
            visit.treated = cams_schema_config.cams_field_key('Visits_Table', 'Treated', row.attributes['Treated'])
            visit.how_treated = cams_schema_config.cams_field_key('Visits_Table', 'How treated', row.attributes['HowTreated'])
            visit.treatment_substance = cams_schema_config.cams_field_key('Visits_Table', 'Treatment substance', row.attributes['TreatmentSubstance'])
            if visit.treatment_substance == 'None':
                visit.treatment_substance = None
            visit.treatment_details = row.attributes['TreatmentDetails']
            visit.visit_status = cams_schema_config.cams_field_key('Visits_Table', 'WeedVisitStatus', row.attributes['WeedVisitStatus'])

            visit.observation_quality = cams_schema_config.cams_field_key('Visits_Table', 'ObservationQuality', row.attributes['ObservationQuality'])
            visit.notes = row.attributes['NotesAndDetails']
            weed_visits.append(visit)

            guid = row.attributes['GUID_visits']
            if location_guid is None:
                location_guid = guid
            elif location_guid != guid:
                raise ValueError(f'''All weed visit records with a single iNat id must be associated with the same feature.
                                 The records with iNatRef = {inat_id} are linked to different features.''')

            query_layer = f"GlobalID='{guid}'"
            rows = cams_interface.connection.query_weed_location_layer_wgs84(query_layer)
            for featureRow in rows.features:
                location = cams_observation.WeedLocation()
                logging.info(f'Found layer row {featureRow}')
                location.object_id = featureRow.attributes['OBJECTID']
                location.global_id = guid
                location.date_first_observed = self.as_datetime(featureRow.attributes['DateDiscovered'])
                location.species = featureRow.attributes['SpeciesDropDown']
                location.data_source = cams_schema_config.cams_field_key('WeedLocations', 'DataSource', featureRow.attributes['SiteSource'])
                location.location_details = featureRow.attributes['LocationInfo']
                location.effort_to_control = featureRow.attributes['Urgency']
                location.current_status = cams_schema_config.cams_field_key('WeedLocations', 'CurrentStatus', featureRow.attributes['ParentStatusWithDomain'])

                # Temporarily until updated from weed visit by database trigger
                location.external_url = featureRow.attributes['iNatURL']

        cams_feature = cams_observation.CamsFeature(featureRow.geometry, location, weed_visits)
        return cams_feature

    def as_datetime(self, date_field):
        return pytz.timezone('Pacific/Auckland').localize(datetime.fromtimestamp(date_field // 1000))
