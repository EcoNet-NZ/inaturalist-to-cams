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
        row_ids = cams_interface.connection.query_weed_visits_table_ids(query_table)
        object_ids = row_ids['objectIds']
        if not object_ids:
            logging.info(f'No existing CAMS feature found for iNaturalist id {inat_id}')
            return None

        logging.info(f'Found existing CAMS feature with {len(object_ids)} visit rows for iNaturalist id {inat_id}')

        latest_object_id = object_ids[len(object_ids)-1]
        weed_visits = []
        location_guid = None

        query_table = f"OBJECTID='{latest_object_id}'"
        logging.info(f'Reading CAMS feature where {query_table}')
        visit_table_row = cams_interface.connection.query_weed_visits_table(query_table).features[0]
        logging.info(f'Found visit table row {visit_table_row}')
        visit = cams_observation.WeedVisit()
        cams_schema_config = config.cams_schema_config
        visit.object_id = visit_table_row.attributes['OBJECTID']
        visit.external_id = visit_table_row.attributes['iNatRef']
        visit.external_url = visit_table_row.attributes['iNaturalistURL']
        visit.date_visit_made = self.as_datetime(visit_table_row.attributes['DateCheck'])
        visit.height = visit_table_row.attributes['Height']
        visit.area = visit_table_row.attributes['Area']
        visit.radius_surveyed = visit_table_row.attributes['CheckedNearbyRadius']
        visit.site_difficulty = cams_schema_config.cams_field_key('Visits_Table', 'Site difficulty', visit_table_row.attributes['SiteDifficulty'])
        visit.follow_up_date = visit_table_row.attributes['DateForReturnVisit']
        visit.phenology = cams_schema_config.cams_field_key('Visits_Table', 'Plant phenology->most common flowering/fruiting reproductive stage', visit_table_row.attributes['Flowering'])
        visit.treated = cams_schema_config.cams_field_key('Visits_Table', 'Treated', visit_table_row.attributes['Treated'])
        visit.how_treated = cams_schema_config.cams_field_key('Visits_Table', 'How treated', visit_table_row.attributes['HowTreated'])
        visit.treatment_substance = cams_schema_config.cams_field_key('Visits_Table', 'Treatment substance', visit_table_row.attributes['TreatmentSubstance'])
        visit.treatment_details = visit_table_row.attributes['TreatmentDetails']
        visit.visit_status = cams_schema_config.cams_field_key('Visits_Table', 'WeedVisitStatus', visit_table_row.attributes['WeedVisitStatus'])
        visit.observation_quality = cams_schema_config.cams_field_key('Visits_Table', 'ObservationQuality', visit_table_row.attributes['ObservationQuality'])
        visit.notes = visit_table_row.attributes['NotesAndDetails']
        weed_visits.append(visit)

        guid = visit_table_row.attributes['GUID_visits']

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

        cams_feature = cams_observation.CamsFeature(featureRow.geometry, location, weed_visits)
        return cams_feature

    def as_datetime(self, date_field):
        return pytz.timezone('Pacific/Auckland').localize(datetime.fromtimestamp(date_field // 1000))
