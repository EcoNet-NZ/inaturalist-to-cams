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

from datetime import datetime
import logging
from arcgis import geometry
from inat_to_cams import cams_interface, cams_reader
from inat_to_cams.cams_writer import CamsWriter

class TestCamsWriter(CamsWriter):
    def __init__(self):
        super().__init__()
    
    def update_feature_geolocation(self, inat_id, lon, lat):
        global_id = None
        geometry = {'x': lon,
                        'y': lat,
                        'spatialReference': {'wkid': 4326, 'latestWkid': 4326}
                    }
        logging.info(f'Updating geolocation of CAMS feature with iNaturalist id {inat_id} geometry: {geometry}')
        reader = cams_reader.CamsReader()
        cams_feature = reader.read_observation(inat_id)
        
        new_layer_row = [{
            'geometry': geometry,
            'attributes': {
            }
        }]
        
        global_id = cams_feature.weed_location.global_id
        object_id = cams_feature.weed_location.object_id
        new_layer_row[0]['attributes']['objectId'] = object_id
        new_layer_row[0]['attributes']['globalId'] = global_id
        logging.info(f'Updating CAMS WeedLocations layer with new geolocation: {new_layer_row}')
        cams_interface.connection.update_weed_location_layer_row(new_layer_row)
    
        return global_id, object_id