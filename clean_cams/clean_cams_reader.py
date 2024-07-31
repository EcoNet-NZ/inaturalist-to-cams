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
from inat_to_cams import cams_interface, cams_feature

class CleanCAMSReader:

    def read_observations( self, query_layer):
      
        rows = cams_interface.connection.query_weed_location_layer(query_layer)
        cams_items = []
           
        logging.info("++++CAMS Feature URLs----------------------")      
        for featureRow in rows.features:                            
            cams_items.append(featureRow.attributes['iNatURL']   )
        return cams_items

    def get_features_with_iNat_URL(self):
        query = f"iNatURL LIKE 'https://www.inaturalist.org/observations%'"
        existing_CAMS_feature = self.read_observations( query)
        return existing_CAMS_feature

    def get_feature_by_id(self, object_id):
        query = f"OBJECTID={object_id}"
        CAMS_feature = self.read_observations( query, 1 )
        return CAMS_feature[0]