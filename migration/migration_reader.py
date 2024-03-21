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

from inat_to_cams import cams_interface, cams_feature, config


class CamsMigrationReader:

    def read_observations(self):
  
        query_layer = f"(iNatLongitude='' OR iNatLongitude is null) AND (iNatURL is not null OR iNatURL ='')"
        rows = cams_interface.connection.query_weed_location_layer_wgs84(query_layer)
        cams_items = []
    
       #@ logging.info(f"Found {len(rows.features)} CAMS features without iNatLong/Lat")
        for featureRow in rows.features:         
            location = cams_feature.WeedLocation()
            location.object_id = featureRow.attributes['OBJECTID']
          
            location.iNaturalist_longitude = featureRow.attributes['iNatLongitude']
            location.iNaturalist_latitude = featureRow.attributes['iNatLatitude']
           
            location.external_url = featureRow.attributes['iNatURL']
           
            cams_items.append(cams_feature.CamsFeature(featureRow.geometry, location,{}))
        return cams_items

    