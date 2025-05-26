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

import datetime
import func_timeout
import logging

from inat_to_cams import config, inaturalist_reader


class iNatObservations():

    def get_observations(self):
        observations = []
        # Set to track unique observation IDs
        unique_observation_ids = set()

        # First, collect all taxon_ids by place_id for non-project configurations
        taxon_ids_by_place = {}
        for config_name, values in config.sync_configuration.items():
            is_project_based = 'project_id' in values
            if not is_project_based and 'taxon_ids' in values:
                place_ids = values['place_ids']
                taxon_ids = values['taxon_ids']

                for place_id in place_ids:
                    if place_id not in taxon_ids_by_place:
                        taxon_ids_by_place[place_id] = set()
                    taxon_ids_by_place[place_id].update(taxon_ids)

        for config_name, values in config.sync_configuration.items():
            # pull in all observations by setting year 2000 timestamp
            timestamp = '2000-01-01T00:00:00+12:00'
            place_ids = values['place_ids']
            is_project_based = 'project_id' in values

            logging.info('=' * 80)

            time_of_previous_update = datetime.datetime.fromisoformat(
                timestamp)

            try:
                if is_project_based:
                    project_id = values['project_id']

                    # Collect taxon_ids to exclude for this project
                    not_taxon_ids = set()
                    for place_id in place_ids:
                        if place_id in taxon_ids_by_place:
                            not_taxon_ids.update(
                                taxon_ids_by_place[place_id])

                    logging.info(
                        f"Finding project '{config_name}' with project_id "
                        f"'{project_id}' and place_ids '{place_ids}' since "
                        f"{timestamp}")
                    if not_taxon_ids:
                        logging.info(f"Excluding taxon_ids: {not_taxon_ids}")

                    config_observations = func_timeout.func_timeout(
                        300,  # seconds
                        inaturalist_reader.INatReader()
                        .get_project_observations_updated_since,
                        args=(place_ids, project_id, time_of_previous_update),
                        kwargs={'not_taxon_ids': list(not_taxon_ids)
                                if not_taxon_ids else None}
                    )
                else:
                    taxon_ids = values['taxon_ids']
                    logging.info(
                        f"Finding '{config_name}' with taxon_ids '{taxon_ids}' "
                        f"and place_ids '{place_ids}' since {timestamp}")

                    config_observations = func_timeout.func_timeout(
                        300,  # seconds
                        inaturalist_reader.INatReader()
                        .get_matching_observations_updated_since,
                        args=(place_ids, taxon_ids, time_of_previous_update)
                    )

                # Only add observations that have a taxon_id and are not duplicates
                valid_observations = []
                for observation in config_observations:
                    # Skip observations with None taxon_id
                    if observation.taxon is None:
                        logging.info(
                            f"Skipping observation {observation.id} with None taxon")
                        continue
                    
                    # Skip duplicates
                    if observation.id not in unique_observation_ids:
                        valid_observations.append(observation)
                        unique_observation_ids.add(observation.id)

                logging.info(
                    f"Found '{len(config_observations)}' observations, "
                    f"{len(valid_observations)} valid and unique from "
                    f"'{config_name}' since {timestamp}")
                
                for observation in valid_observations:
                    observations.append(str(observation.id))
            except func_timeout.FunctionTimedOut:
                logging.error(
                    f"Timed out fetching observations for {config_name}")
                continue

        logging.info(f"Total unique observations: {len(unique_observation_ids)}")
        return observations
