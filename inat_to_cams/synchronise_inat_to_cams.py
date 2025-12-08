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

    def sync_single_observation(self, observation_id):
        observation = inaturalist_reader.INatReader().get_observation_with_id(observation_id)
        try:
            self.sync_observation(observation)
        except exceptions.InvalidObservationError:
            logging.info(f'Ignoring invalid observation {observation.id}')

    def sync_updated_observations(self):
        new_observations_by_project = {}
        # Keep track of all observation IDs to avoid double counting
        all_processed_observation_ids = set()

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
            p = pathlib.Path(
                values['file_prefix'] + '_time_of_last_update.txt')

            if p.exists():
                timestamp = p.read_text()
            else:
                timestamp = '2000-01-01T00:00:00+12:00'

            place_ids = values['place_ids']
            is_project_based = 'project_id' in values

            if is_project_based:
                project_id = values['project_id']

                # Collect taxon_ids to exclude for this project
                not_taxon_ids = set()
                for place_id in place_ids:
                    if place_id in taxon_ids_by_place:
                        not_taxon_ids.update(taxon_ids_by_place[place_id])

                logging.info('=' * 80)
                logging.info(
                    f"Syncing project '{config_name}' with project_id '{project_id}' "
                    f"and place_ids '{place_ids}' since {timestamp}")
                if not_taxon_ids:
                    logging.info(
                        f"Excluding taxon_ids: {not_taxon_ids}")
            else:
                taxon_ids = values['taxon_ids']
                logging.info('=' * 80)
                logging.info(
                    f"Syncing '{config_name}' with taxon_ids '{taxon_ids}' "
                    f"and place_ids '{place_ids}' since {timestamp}")

            time_of_previous_update = datetime.datetime.fromisoformat(timestamp)
            logging.info("Previous update: " + str(time_of_previous_update))
            time_of_latest_update = time_of_previous_update

            try:
                if is_project_based:
                    observations = func_timeout.func_timeout(
                        120,  # seconds
                        inaturalist_reader.INatReader().get_project_observations_updated_since,
                        args=(place_ids, project_id, time_of_previous_update),
                        kwargs={'not_taxon_ids': list(not_taxon_ids) if not_taxon_ids else None}
                    )
                else:
                    observations = func_timeout.func_timeout(
                        120,  # seconds
                        inaturalist_reader.INatReader().get_matching_observations_updated_since,
                        args=(place_ids, taxon_ids, time_of_previous_update)
                    )
            except func_timeout.FunctionTimedOut:
                logging.error(f"Timed out fetching observations for {config_name}")
                continue

            # Filter out observations that have already been processed in other configs
            unique_observations = []
            for obs in observations:
                if obs.id not in all_processed_observation_ids:
                    unique_observations.append(obs)
                    all_processed_observation_ids.add(obs.id)

            logging.info(
                f"{str(len(observations))} new or updated observations for {config_name}")
            logging.info(
                f"{str(len(unique_observations))} unique observations (not in other configs)")
            
            # Store only the count of unique observations
            new_observations_by_project[config_name] = len(unique_observations)

            self.setup_summary_log_to_print_config_name(config_name)

            for observation in unique_observations:
                try:
                    self.sync_observation(observation)
                except exceptions.InvalidObservationError:
                    logging.info(
                        f'Ignoring invalid observation {observation.id}')

                time_of_latest_update = max(
                    time_of_latest_update, observation.updated_at)

            if time_of_latest_update > time_of_previous_update:
                p.write_text(time_of_latest_update.isoformat())

        # Add a total count of unique observations
        new_observations_by_project['TOTAL (unique observations)'] = len(all_processed_observation_ids)
        
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

        # Get complete observation data with updater_id for accurate RecordedBy tracking
        observation_id = observation.id if hasattr(observation, 'id') else observation.get('id')
        observation_complete = inaturalist_reader.INatReader.get_observation_complete_data(observation_id)

        inat_to_cams_translator = translator.INatToCamsTranslator()
        cams_feature = inat_to_cams_translator.translate(inat_observation, observation_complete)

        if not cams_feature:
            return

        writer = cams_writer.CamsWriter()
        global_id = writer.write_observation(cams_feature)

        return cams_feature, global_id


synchroniser = INatToCamsSynchroniser()
