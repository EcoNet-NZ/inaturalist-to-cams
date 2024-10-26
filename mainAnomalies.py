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
from anomaly_finder import cams_inat_anomaly_finder


def main():

    logging.info('Finding anomalies between iNaturalist and CAMS, eg iNaturalist observation changes or deletions')
    anomaly_finder = cams_inat_anomaly_finder.CamsInatAnomalyFinder()
    anomaly_count = anomaly_finder.find_anomalies()
    sys.exit(1 if anomaly_count > 0 else 0)


main()
