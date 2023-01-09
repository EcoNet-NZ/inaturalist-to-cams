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
import pyinaturalist

from inat_to_cams import cams_interface, config, exceptions, inaturalist_reader, synchroniser


def check_cams_schema():
    schema_comparator = cams_interface.CamsSchemaComparator()
    schema_comparator.compare('WeedLocations')
    schema_comparator.compare('Visits_Table')


def delete_records():
    delete_layer_rows__with_id_over = 57000
    delete_table_rows_with_id_over = 100000
    yn = input(f'WARNING: Do you want to delete WeedLocations layer rows with id over {delete_layer_rows__with_id_over} and Weed_Visits table rows with id over {delete_table_rows_with_id_over} (y/n)? ')
    if yn == 'y':
        cams_interface.connection.delete_location_rows_with_object_id_gt(delete_layer_rows__with_id_over)
        cams_interface.connection.delete_visit_rows_with_object_id_gt(delete_table_rows_with_id_over)
    else:
        logging.info(f"Skipping deletion based on manual input of '{yn}'")


def sync_single_observation():
    inat_id = 143701827
    cams_interface.connection.delete_rows_between(inat_id, inat_id)
    observation_in_json = pyinaturalist.get_observation(inat_id)
    synchroniser.INatToCamsSynchroniser().sync_observation(pyinaturalist.Observation.from_json(observation_in_json))


def sync_updated_observations():
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

        for observation in observations:
            try:
                synchroniser.INatToCamsSynchroniser().sync_observation(observation)
            except exceptions.InvalidObservationError:
                logging.info(f'Ignoring invalid observation {observation.id}')

            time_of_latest_update = max(time_of_latest_update, observation.updated_at)

        if time_of_latest_update > time_of_previous_update:
            p.write_text(time_of_latest_update.isoformat())

    return new_observations_by_project


# delete_records()
check_cams_schema()
observation_counts = sync_updated_observations()

logging.info('Completed synchronisation: ')
for count in observation_counts.items():
    logging.info(f'* {count[0]:<35}{count[1]:>20} observations added')
