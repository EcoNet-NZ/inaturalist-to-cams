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

import datetime
import func_timeout
import logging
import pathlib
import re
import pyinaturalist
from migration import migration_reader, cams_migration_writer 
#from inat_to_cams import cams_writer, config, exceptions, inaturalist_reader, summary_logger, translator


class copyiNatLocationsToCAMS():
    # def copy_single_observation(inat_id):
    #     cams_interface.connection.delete_rows_between(inat_id, inat_id)
    #     observation_in_json = pyinaturalist.get_observation(inat_id)
    #     self.sync_observation(pyinaturalist.Observation.from_json(observation_in_json))

    def extract_observation_id(self, url):
        observation_id = None
       
        # Extract observation ID from the URL using regex
        match = re.search(r'/observations/(\d+)', url)
        if match:
            observation_id = match.group(1)            
        
        else:
            logging.warning(f"Malformed URL: {url}")
        return observation_id

    def get_observation_from_id(self, observation_id):                
        observation = pyinaturalist.get_observation(observation_id)       
        return observation
    
    def copyiNatLocations_to_existing_CAMS_features(self):
        observation_count = 0
        #Get all the CAMS features with an empty iNaturalist Location and an iNatURL
        camsReader = migration_reader.CamsMigrationReader()
        existing_CAMS_features = camsReader.read_observations()
        logging.info(f"Found {len(existing_CAMS_features)} CAMS features without iNatLong/Lat")
        #Extract the iNaturalist IDs
        

        #For each CamsFeature, extract the iNat observation ID and get the Original iNat observation location
        features_to_update = []
        for feature in existing_CAMS_features[:6]:
            observationID = self.extract_observation_id(feature.weed_location.external_url)
            if observationID != None:
                print(f"Getting observation with ID:{observationID}")
                observation = self.get_observation_from_id(observationID)
                if observation:
                    location = observation['location']
                    logging.info(f"Observation {observationID} found. Located at {location}")
                    feature.weed_location.iNaturalist_latitude = location[0]
                    feature.weed_location.iNaturalist_longitude = location[1]
                    features_to_update.append(feature)
                    observation_count +=1
                else:
                    logging.error(f"observation not found for {observationID}")
                    
        for feature in features_to_update:
           
            
            #Now save the location to CAMS 
            cams_writer = cams_migration_writer.CamsMigrationWriter()
            cams_writer.write_feature(feature, )
                    
        return observation_count
   
locationCopier = copyiNatLocationsToCAMS()