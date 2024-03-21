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

import datetime
import logging
import pytz
import sys
from migration import migrate




def main():
    #if len(sys.argv) > 2:
        #server_timezone = pytz.timezone("Pacific/Auckland")
        #server_time = datetime.datetime.now(server_timezone)  # you could pass *tz* directly
        
    copier = migrate.copyiNatLocationsToCAMS()
    copy_count = copier.copyiNatLocations_to_existing_CAMS_features()

    logging.info(f'Completed location copy: {copy_count}')
    

main()
