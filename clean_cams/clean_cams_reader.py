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
from inat_to_cams import cams_interface


class CleanCAMSReader:

    def read_observations(self, query_layer, column):

        rows = cams_interface.connection.query_weed_location_layer(query_layer)
        cams_items = []
        for featureRow in rows.features:
            cams_items.append(featureRow.attributes[column])
        return cams_items

    def get_features_with_iNat_URL(self):
        query = "iNatURL LIKE 'https://www.inaturalist.org/observations%'"
        existing_CAMS_feature = self.read_observations(query, 'iNatURL')
        logging.info(f"++++ Found {len(existing_CAMS_feature)} CAMS Features with an iNat URL----------------------")      
        return existing_CAMS_feature

    def get_objectid_from_iNat_ID(self, id):
        query = f"iNatURL = 'https://www.inaturalist.org/observations/{id}'"
        feature = self.read_observations(query, 'OBJECTID')
        return feature
