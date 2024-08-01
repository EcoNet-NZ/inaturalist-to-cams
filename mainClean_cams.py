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
from clean_cams import cams_cleanup


def main():
    
    logging.info(f'Cleaing old and unused CAMS records for deleted or changed iNaturalist observations')
    cleaner = cams_cleanup.cleanCAMS()
    clean_count = cleaner.clean()
    logging.info(f'Completed clean up. Removed {clean_count} CAMS records')


main()
