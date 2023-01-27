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

import logging

run_details_header = None
config_name = None
config_name_written = False
log_header_written = False


def write_log_header():
    logging.getLogger('summary').info('---')  # horizontal line in GitHub Flavored Markdown
    logging.getLogger('summary').info('')

    if run_details_header:
        logging.getLogger('summary').info(f'{run_details_header}')
        logging.getLogger('summary').info('')

    logging.getLogger('summary').info('|Sync Event|Object Id|Species|Status|iNaturalist Id|')
    logging.getLogger('summary').info('|----------|---------|-------|------|--------------|')


def write_config_name():
    if config_name:
        logging.getLogger('summary').info(f'## {config_name}')


def write_summary_log(cams_observation, object_id, existing_feature, new_weed_visit_record, weed_geolocation_modified, weed_location_modified, weed_visit_modified):
    if not existing_feature:
        description = 'New weed'
    else:
        updates = []
        if weed_geolocation_modified:
            updates.append('Geolocation updated')
        if weed_location_modified:
            updates.append('Weed record updated')
        if weed_visit_modified:
            if new_weed_visit_record:
                updates.append('Visit record added')
            else:
                updates.append('Visit record updated')
        description = ', '.join(updates)
    logging.getLogger('summary').info(f'|{description}|**{object_id}**|{cams_observation.weed_location.species}|{cams_observation.weed_location.current_status}|[{cams_observation.weed_visits[0].external_id}]({cams_observation.weed_visits[0].external_url})|')
