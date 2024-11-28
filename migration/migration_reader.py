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


class CamsMigrationReader:

    def read_observations( self, query_layer, max_record_count):

        rows = cams_interface.connection.query_weed_location_layer_limit_records(query_layer, max_record_count)
        cams_items = []

        logging.info("++++CAMS ROWS----------------------")
        for featureRow in rows.features:
            logging.info(f"{featureRow}")
            logging.info("----------------------")
            location = cams_feature.WeedLocation()
            location.object_id = featureRow.attributes['OBJECTID']
            location.image_urls = featureRow.attributes['ImageURLs']
            location.image_attribution = featureRow.attributes['ImageAttribution']
            location.location_accuracy = featureRow.attributes['LocationAccuracy']
            location.external_url = featureRow.attributes['iNatURL']
            cams_items.append(cams_feature.CamsFeature(featureRow.geometry, location,{}))
        return cams_items

    def get_features_without_iNat_photo(self, max_record_count):
        query = f"(ImageURL='' OR ImageURL is null) AND (iNatURL LIKE 'https://www.inaturalist.org/observations%')"
        existing_CAMS_feature = self.read_observations( query, max_record_count )
        return existing_CAMS_feature

    def get_feature_by_id(self, object_id):
        query = f"OBJECTID={object_id}"
        CAMS_feature = self.read_observations(query, 1)
        return CAMS_feature[0]

    def get_feature_by_inat_id(self, inat_id):
        query = f"iNatURL='https://www.inaturalist.org/observations/{inat_id}'"
        CAMS_feature = self.read_observations(query, 1)
        if not CAMS_feature or len(CAMS_feature) == 0:
            return None
        return CAMS_feature[0]
