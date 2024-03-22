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
import sys
from migration import migrate

DEFAULT_MIGRATION_COUNT = 5


def main(how_many_records_to_migrate):
    
    logging.info(f'Running Migration for the first {how_many_records_to_migrate} records')
    copier = migrate.copyiNatLocationsToCAMS()
    copy_count = copier.copyiNatLocations_to_existing_CAMS_features(how_many_records_to_migrate)
    logging.info(f'Completed location copy: {copy_count}')

args = sys.argv[1:]
if len(args) >= 1:
    param1 = args[0]
else:
    param1 = DEFAULT_MIGRATION_COUNT

main(param1)
