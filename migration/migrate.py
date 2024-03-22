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
import re
import pyinaturalist
from migration import migration_reader, cams_migration_writer 

class copyiNatLocationsToCAMS(): 

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
    
    def copyiNatLocations_to_existing_CAMS_features(self, migration_max_record_count):
        update_count = 0
        report = []
        report.append("***************** Update Report **************")
        cams_writer = cams_migration_writer.CamsMigrationWriter()

        #Get the CAMS features with an empty iNaturalist Location and a valid iNatURL      
        camsReader = migration_reader.CamsMigrationReader()       
        existing_CAMS_features = camsReader.get_features_without_iNat_location(migration_max_record_count)

        message = f"Found {len(existing_CAMS_features)} CAMS feature without iNatLong/Lat"
        logging.info(message)        
        report.append(message)
        
        #For each CamsFeature, extract the iNat observation ID and get the Original iNat observation location     
        for feature in existing_CAMS_features:
            observationID = self.extract_observation_id(feature.weed_location.external_url)
            if observationID != None:
                
                observation = self.get_observation_from_id(observationID)
                if observation:
                    report.append(f"CAMS Feature[{update_count+1}]: object_id:{feature.weed_location.object_id},  iNatID:{observationID} URL: {feature.weed_location.external_url}")
                    location = observation['location']
                    logging.info(f"Observation {observationID} found. Located at {location}")
                    feature.weed_location.iNaturalist_latitude = location[0]
                    feature.weed_location.iNaturalist_longitude = location[1]                              

                    #Now save the location to CAMS                                      
                    cams_writer.write_feature(feature ) 
                    report.append(f"Updated iNatLocation for CAMS object_id {feature.weed_location.object_id}")

                    #read it back to validate update
                    updated_feature = camsReader.get_feature_by_id(feature.weed_location.object_id)
                    assert updated_feature.weed_location.iNaturalist_latitude == location[0], f"iNatLocation(lat) for {feature.weed_location.object_id} ({updated_feature.weed_location.iNaturalist_latitude}) was not updated to {location[0]}"
                    assert updated_feature.weed_location.iNaturalist_longitude == location[1],f"iNatLocation(long) for {feature.weed_location.object_id} ({updated_feature.weed_location.iNaturalist_longitude}) was not updated to {location[1]}"
                    report.append("")
                    update_count +=1
                else:
                    message = f"iNaturalist observation {observationID} not found --- URL: {feature.weed_location.external_url}"
                    logging.error(message)
                    report.append(message)
            else:
                message = f"iNaturalist ID not found in this URL: {feature.weed_location.external_url} (SKIPPING FEATURE)"
                logging.error(message)
                report.append(message)        

        report.append(f"Updated {update_count} CAMS features successfully")
        report.append("*************** REPORT ENDS *******************")

        for line in report:
            print(line)
        return update_count
   
locationCopier = copyiNatLocationsToCAMS()