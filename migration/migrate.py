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
import datetime
import func_timeout
import re
import pyinaturalist
from pyinaturalist.exceptions import ObservationNotFound
from migration import migration_reader, cams_migration_writer
from inat_to_cams import inaturalist_reader, config


class CopyiNatDetailsToCAMS():

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
        try:
            # observation = pyinaturalist.get_observation(observation_id)
            client = pyinaturalist.iNatClient()
            observation = client.observations(observation_id)

        except ObservationNotFound:
            return None

        return observation
    
    def copyiNatDetails_to_existing_CAMS_features(self):
        update_count = 0

        for config_name, values in config.sync_configuration.items():

            # pull in all observations by setting year 2000 timestamp
            timestamp = '2000-01-01T00:00:00+12:00'

            taxon_ids = values['taxon_ids']
            place_ids = values['place_ids']

            logging.info('=' * 80)
            logging.info(f"Finding '{config_name}' with taxon_ids '{taxon_ids}' and place_ids '{place_ids}' since {timestamp}")

            time_of_previous_update = datetime.datetime.fromisoformat(timestamp)

            taxonObservations = func_timeout.func_timeout(
                120,  # seconds
                inaturalist_reader.INatReader().get_matching_observations_updated_since,
                args=(place_ids, taxon_ids, time_of_previous_update)
            )

            logging.info(f"Found '{len(taxonObservations)}' observations from '{config_name}' with taxon_ids '{taxon_ids}' and place_ids '{place_ids}' since {timestamp}")
            for observation in taxonObservations:
                update_count += self.update_cams_feature_from(observation)

        print(f"Updated {update_count} CAMS features successfully")
        print("*************** REPORT ENDS *******************")

        return update_count

    def update_cams_feature_from(self, observation):
        feature = migration_reader.CamsMigrationReader().get_feature_by_inat_id(observation.id)
        if feature:
            # print(observation)
            # print('---')
            if observation.photos:
                # print(f"CAMS Feature: object_id:{feature.weed_location.object_id},  URL: {feature.weed_location.external_url}")
                # Get the URL and attribution
                first_photo = observation.photos[0]
                feature.weed_location.image_url = first_photo.url.replace("square.", "large.")
                feature.weed_location.image_attribution = first_photo.attribution

                # Now save the location to CAMS                                      
                cams_migration_writer.CamsMigrationWriter().write_feature_image_fields(feature)
                logging.info(f"Updated photo for CAMS object_id {feature.weed_location.object_id} with iNat id {observation.id} to {feature.weed_location.image_url}")
                return 1
            else:
                logging.info(f"No photo for inat id {observation.id}")
                return 0
        else:
            logging.info(f"Feature not found for inat id {observation.id}")
            return 0
