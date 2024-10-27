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
import logging
import pytz
import sys

from inat_to_cams import cams_interface, synchronise_inat_to_cams, summary_logger


def check_cams_schema():
    schema_comparator = cams_interface.CamsSchemaComparator()
    schema_comparator.compare('WeedLocations')
    schema_comparator.compare('Visits_Table')


def main():
    if len(sys.argv) != 2:
        print("Usage: python mainSyncSingle <observation_id(s)>")
        sys.exit(1)

    observation_ids = sys.argv[1]

    server_timezone = pytz.timezone("Pacific/Auckland")
    server_time = datetime.datetime.now(server_timezone)  # you could pass *tz* directly
    summary_logger.run_details_header = f"# Run mainSyncObservationList {observation_ids} \n{server_time.strftime('%Y-%m-%d %H:%M')}"

    check_cams_schema()

    for observation_id in observation_ids.split(','):
        logging.info(f"Attempting to sync observation {observation_id}")
        synchronise_inat_to_cams.synchroniser.sync_single_observation(observation_id)
    logging.info('Completed synchronisation')


main()
