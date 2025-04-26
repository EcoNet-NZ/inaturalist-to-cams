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

import re
from anomaly_finder import cams_anomaly_reader, inat_anomaly_reader

base_URL = "https://experience.arcgis.com/experience/847c1702f6ae4b9daadba78dd58bef14/page/Weeds-Map-0_7k#data_s=id%3AdataSource_47-18a1109cdff-layer-9-18e49b73cdf-layer-45%3A"


class CamsInatAnomalyFinder():

    def extract_observation_id(self, url):
        observation_id = None

        # Extract observation ID from the URL using regex
        match = re.search(r'/observations/(\d+)', url)
        if match:
            observation_id = match.group(1)                    
        else:
            logging.warning(f"Malformed URL: {url}")
        return observation_id 

    def logAndReport(self, report, message):
        logging.info(message)        
        report.append(message)

    def find_anomalies(self):
        report = []
        existing_CAMS_features = []
        report.append("***************** Anomaly Report **************")

        # Get all the CAMS features with an iNaturalist URL
        camsReader = cams_anomaly_reader.CAMSAnomalyReader()
        all_synchronised_CAMS_features = camsReader.get_features_with_iNat_URL()
        duplicate_CAMS_features = find_duplicates(all_synchronised_CAMS_features)
        for url in all_synchronised_CAMS_features:
            existing_CAMS_features.append(self.extract_observation_id(url))

        self.logAndReport(report, f"Found {len(existing_CAMS_features)} CAMS features ")

        # Now get all the iNat observations
        obs = inat_anomaly_reader.iNatObservations()
        existing_iNat_observations = obs.get_observations()
        self.logAndReport(report, f"Found {len(existing_iNat_observations)} iNat observations")

        # subtract one list from the other to get CAMS features that are no longer in iNat
        setCams = set(existing_CAMS_features)
        setiNat = set(existing_iNat_observations)

        inCamsOnly = setCams - setiNat
        inINatOnly = setiNat - setCams
        self.logAndReport(report, f"{len(duplicate_CAMS_features)} features in CAMS with duplicate iNatURLs")
        self.logAndReport(report, f"{len(inCamsOnly)} found in CAMS and not iNaturalist")
        self.logAndReport(report, f"{len(inINatOnly)} found in iNaturalist and not CAMS")

        if duplicate_CAMS_features:
            for url in duplicate_CAMS_features:
                iNat_id = self.extract_observation_id(url)
                object_ids = camsReader.get_objectid_from_iNat_ID(iNat_id)
                print(f"iNat observation {iNatUrl(iNat_id)} duplicated by CAMS weed instances with OBJECTID {object_ids}")
                
                # For each object_id, get the visit records and print those with more than 1
                for object_id in object_ids:
                    visits_count = camsReader.get_visit_count_for_weed_location(object_id)
                    status = camsReader.get_current_status_for_weed_location(object_id)
                    if visits_count > 1:
                        print(f"  - CAMS ObjectID {object_id} has {visits_count} visit records with status: {status}")
                    else:
                        print(f"  - CAMS ObjectID {object_id} has {visits_count} visit record with status: {status}")
                

        if inCamsOnly:
            for iNat_id in inCamsOnly:
                object_ids = camsReader.get_objectid_from_iNat_ID(iNat_id)
                print(f"Weed instance in CAMS  {camsUrl(object_ids[0])} not found in iNaturalist {iNatUrl(iNat_id)}")

        if inINatOnly:
            for iNat_id in inINatOnly:
                print(f"iNaturalist observations {iNatUrl(iNat_id)} not found in CAMS")

        report.append("*************** REPORT ENDS *******************")

        for line in report:
            print(line)

        anomaly_count = len(duplicate_CAMS_features) + len(inCamsOnly) + len(inINatOnly)
        return anomaly_count

def camsUrl(cams_id):
    return f"https://cams.econet.nz/weed/{cams_id}"

def iNatUrl(inat_id):
    return f"https://inaturalist.org/observations/{inat_id}"

def find_duplicates(lst):
    seen = set()
    duplicates = set()

    for item in lst:
        if item in seen:
            duplicates.add(item)
        else:
            seen.add(item)

    return list(duplicates)
