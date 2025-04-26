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
import argparse
from anomaly_finder import cams_inat_anomaly_finder


def main():
    parser = argparse.ArgumentParser(
        description='Find anomalies between iNaturalist and CAMS'
    )
    parser.add_argument(
        '--delete-zero-visit-duplicates', 
        action='store_true',
        help='Delete duplicate CAMS features with 0 visit records'
    )
    parser.add_argument(
        '--no-dry-run', 
        action='store_true',
        help='Actually perform deletion (default is simulation only)'
    )
    args = parser.parse_args()

    logging.info('Finding anomalies between iNaturalist and CAMS')
    anomaly_finder = cams_inat_anomaly_finder.CamsInatAnomalyFinder()
    anomaly_count = anomaly_finder.find_anomalies(
        delete_zero_visit_duplicates=args.delete_zero_visit_duplicates,
        dry_run=not args.no_dry_run
    )
    sys.exit(1 if anomaly_count > 0 else 0)


if __name__ == "__main__":
    main()
