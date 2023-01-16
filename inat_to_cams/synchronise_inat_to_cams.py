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
import pathlib

from inat_to_cams import cams_writer, config, exceptions, inaturalist_reader, summary_logger, translator


class INatToCamsSynchroniser():
    # def sync_single_observation(inat_id):
    #     cams_interface.connection.delete_rows_between(inat_id, inat_id)
    #     observation_in_json = pyinaturalist.get_observation(inat_id)
    #     self.sync_observation(pyinaturalist.Observation.from_json(observation_in_json))

    def sync_updated_observations(self):
        new_observations_by_project = {}

        for config_name, values in config.sync_configuration.items():
            p = pathlib.Path(values['file_prefix'] + '_time_of_last_update.txt')

            if p.exists():
                timestamp = p.read_text()
            else:
                timestamp = '2000-01-01T00:00:00+12:00'

            taxon_ids = values['taxon_ids']
            place_ids = values['place_ids']

            logging.info('=' * 80)
            logging.info(f"Syncing '{config_name}' with taxon_ids '{taxon_ids}' and place_ids '{place_ids}' since {timestamp}")

            time_of_previous_update = datetime.datetime.fromisoformat(timestamp)
            logging.info("Previous update: " + str(time_of_previous_update))
            time_of_latest_update = time_of_previous_update

            observations = func_timeout.func_timeout(
                120,  # seconds
                inaturalist_reader.INatReader().get_matching_observations_updated_since,
                args=(place_ids, taxon_ids, time_of_previous_update)
            )

            logging.info(f"{str(len(observations))} new or updated observations for {config_name}")
            new_observations_by_project[config_name] = len(observations)

            self.setup_summary_log_to_print_config_name(config_name)

            for observation in observations:
                try:
                    self.sync_observation(observation)
                except exceptions.InvalidObservationError:
                    logging.info(f'Ignoring invalid observation {observation.id}')

                time_of_latest_update = max(time_of_latest_update, observation.updated_at)

            if time_of_latest_update > time_of_previous_update:
                p.write_text(time_of_latest_update.isoformat())

        return new_observations_by_project

    def setup_summary_log_to_print_config_name(self, config_name):
        summary_logger.config_name = config_name
        summary_logger.config_name_written = False

    def sync_observation(self, observation):
        logging.info('-' * 80)
        logging.info(f'Syncing iNaturalist observation {observation}')
        inat_observation = inaturalist_reader.INatReader.flatten(observation)
        logging.info(f'Observed on {inat_observation.observed_on}')

        if not inat_observation:
            return

        inat_to_cams_translator = translator.INatToCamsTranslator()
        cams_observation = inat_to_cams_translator.translate(inat_observation)

        if not cams_observation:
            return

        writer = cams_writer.CamsWriter()
        global_id = writer.write_observation(cams_observation)

        return cams_observation, global_id



synchroniser = INatToCamsSynchroniser()