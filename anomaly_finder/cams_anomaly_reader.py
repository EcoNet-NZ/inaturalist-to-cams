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

import logging
from inat_to_cams import cams_interface, config


class CAMSAnomalyReader:

    def read_observations(self, query_layer, column):

        rows = cams_interface.connection.query_weed_location_layer(query_layer)
        cams_items = []
        for featureRow in rows.features:
            cams_items.append(featureRow.attributes[column])
        return cams_items

    def get_features_with_iNat_URL(self):
        query = "iNatURL LIKE 'https://www.inaturalist.org/observations%'"
        existing_CAMS_feature = self.read_observations(query, 'iNatURL')
        logging.info(
            f"++++ Found {len(existing_CAMS_feature)} CAMS Features "
            f"with an iNat URL----------------------"
        )      
        return existing_CAMS_feature

    def get_objectid_from_iNat_ID(self, id):
        query = f"iNatURL = 'https://www.inaturalist.org/observations/{id}'"
        feature = self.read_observations(query, 'OBJECTID')
        return feature
        
    def get_visit_count_for_weed_location(self, object_id):
        # First get the GlobalID of the weed location
        query = f"OBJECTID = {object_id}"
        rows = cams_interface.connection.query_weed_location_layer(query)
        
        if not rows.features:
            return 0
            
        global_id = rows.features[0].attributes.get('GlobalID')
        if not global_id:
            return 0
            
        # Now count visits with that GlobalID
        query_table = f"GUID_visits = '{global_id}'"
        count = cams_interface.connection.table.query(
            where=query_table, 
            return_count_only=True
        )
        return count
        
    def get_current_status_for_weed_location(self, object_id):
        query = f"OBJECTID = {object_id}"
        rows = cams_interface.connection.query_weed_location_layer(query)
        
        if not rows.features:
            return "Unknown"
            
        status_code = rows.features[0].attributes.get('ParentStatusWithDomain')
        
        # Map status code to friendly name
        cams_schema_config = config.cams_schema_config
        try:
            status = cams_schema_config.cams_field_key(
                'WeedLocations', 
                'CurrentStatus', 
                status_code
            )
            return status
        except Exception:
            return f"Unknown ({status_code})"
