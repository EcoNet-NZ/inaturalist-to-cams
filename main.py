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
import sys

from inat_to_cams import cams_interface, synchronise_inat_to_cams


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


def main():
    # if len(sys.argv) > 1:
    #     print_summary(sys.argv[1])
    # delete_records()
    check_cams_schema()
    observation_counts = synchronise_inat_to_cams.synchroniser.sync_updated_observations()

    logging.info('Completed synchronisation: ')
    for count in observation_counts.items():
        logging.info(f'* {count[0]:<35}{count[1]:>20} observations added')



main()
