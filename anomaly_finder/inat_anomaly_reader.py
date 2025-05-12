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

        for config_name, values in config.sync_configuration.items():

            # pull in all observations by setting year 2000 timestamp
            timestamp = '2000-01-01T00:00:00+12:00'

            taxon_ids = values['taxon_ids']
            place_ids = values['place_ids']

            logging.info('=' * 80)
            logging.info(f"Finding '{config_name}' with taxon_ids '{taxon_ids}' and place_ids '{place_ids}' since {timestamp}")

            time_of_previous_update = datetime.datetime.fromisoformat(timestamp)

            taxonObservations = func_timeout.func_timeout(
                300,  # seconds
                inaturalist_reader.INatReader().get_matching_observations_updated_since,
                args=(place_ids, taxon_ids, time_of_previous_update)
            )
            logging.info(f"Found '{len(taxonObservations)}' observations from '{config_name}' with taxon_ids '{taxon_ids}' and place_ids '{place_ids}' since {timestamp}")
            for observation in taxonObservations:
                observations.append(str(observation.id))

        return observations
