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

from datetime import datetime
import logging
import re

from arcgis import geometry

from inat_to_cams import cams_feature, config


class INatToCamsTranslator:
    @staticmethod
    def sanitiseHTML(html):
        if html is not None:
            # issue #86: URLs with an '=' within are not supported. Remove the reference and add a warning.
            html = re.sub(
                r'<a\s+href="[^"]*=[^"]*".*?>.*?</a>', 
                '(INVALID URL DETECTED - see iNaturalist link for full notes)', 
                html)

        return html
    
    def translate(self, inat_observation):
        geolocation = geometry.Point({'x': inat_observation.location.x,
                                      'y': inat_observation.location.y,
                                      'spatialReference': {'wkid': 4326}
                                      })

        cams_taxon = None
        preferred_common_name = None
        scientific_name = None

        for taxon in reversed(inat_observation.taxon_lineage):
            cams_taxon = config.taxon_mapping.get(str(taxon))
            if cams_taxon is not None:
                break

        if cams_taxon is None:
            # For unmapped taxa, use "OTHER" and store the details
            logging.info(
                f'Unmapped taxon for observation {inat_observation.id} '
                f'with lineage {inat_observation.taxon_lineage}')
            cams_taxon = "OTHER"
            
            # Get the taxon name details from the observation
            if (hasattr(inat_observation, 'taxon_preferred_common_name') and 
                    inat_observation.taxon_preferred_common_name):
                preferred_common_name = inat_observation.taxon_preferred_common_name
            
            if (hasattr(inat_observation, 'taxon_name') and 
                    inat_observation.taxon_name):
                scientific_name = inat_observation.taxon_name

        (visit_date, visit_status) = self.calculate_visit_date_and_status(inat_observation)

        weed_location = cams_feature.WeedLocation()
        weed_location.date_first_observed = self.as_local_datetime(inat_observation.observed_on)
        weed_location.species = cams_taxon
        # If using OTHER, store the details in OtherWeedDetails
        if cams_taxon == "OTHER":
            if preferred_common_name:
                weed_location.other_weed_details = preferred_common_name
                if scientific_name:
                    weed_location.other_weed_details += f" ({scientific_name})"
            elif scientific_name:
                weed_location.other_weed_details = scientific_name
            else:
                weed_location.other_weed_details = "Unknown species from iNaturalist"
                
        weed_location.data_source = 'iNaturalist_v2'
        weed_location.location_details = inat_observation.location_details
        weed_location.iNaturalist_longitude = inat_observation.location.x
        weed_location.iNaturalist_latitude = inat_observation.location.y
        weed_location.location_accuracy = inat_observation.location_accuracy
        weed_location.image_urls = inat_observation.image_urls
        weed_location.image_attribution = inat_observation.image_attribution
        weed_location.external_url = f'https://www.inaturalist.org/observations/{inat_observation.id}'

        # If we're not writing a new weed visit, the following weed_location fields will be reset in cams_writer.write_observation
        effort_to_control = inat_observation.effort_to_control
        if effort_to_control:
            effort_to_control = int(effort_to_control[:1])
        else:
            effort_to_control = 1   # Default to 1

        weed_location.effort_to_control = effort_to_control
        weed_location.current_status = visit_status


        weed_visit = cams_feature.WeedVisit()
        weed_visit.external_id = str(inat_observation.id)
        weed_visit.external_url = f'https://www.inaturalist.org/observations/{inat_observation.id}'
        weed_visit.notes = INatToCamsTranslator.sanitiseHTML(inat_observation.description) 
        weed_visit.height = inat_observation.height
        weed_visit.area = inat_observation.area
        weed_visit.radius_surveyed = inat_observation.radius_surveyed
        weed_visit.date_visit_made = self.as_local_datetime(visit_date)
        weed_visit.observation_quality = inat_observation.quality_grade
        weed_visit.site_difficulty = inat_observation.site_difficulty
        weed_visit.follow_up_date = inat_observation.follow_up_date
        weed_visit.phenology = inat_observation.phenology
        weed_visit.visit_status = visit_status
        weed_visit.treated = inat_observation.treated
        weed_visit.how_treated = inat_observation.how_treated
        weed_visit.treatment_substance = inat_observation.treatment_substance
        if weed_visit.treatment_substance == 'None':
            weed_visit.treatment_substance = None
        weed_visit.treatment_details = inat_observation.treatment_details

        return cams_feature.CamsFeature(geolocation, weed_location, weed_visit)

    def as_local_datetime(self, date_field):
        if not date_field:
            return None
        timestamp = datetime.fromisoformat(date_field)
        naive_datetime = timestamp.replace(tzinfo=None)
        assert naive_datetime.tzinfo is None
        return naive_datetime

    def calculate_visit_date_and_status(self, inat_observation):
        date_first_observed = inat_observation.observed_on
        date_controlled = inat_observation.date_controlled
        date_of_status_update = inat_observation.date_of_status_update

        if date_controlled and date_of_status_update:
            if date_controlled > date_of_status_update:
                visit_date = date_controlled
            else:
                visit_date = date_of_status_update
        elif date_controlled:
            visit_date = date_controlled
        elif date_of_status_update:
            visit_date = date_of_status_update
        else:
            visit_date = date_first_observed

        visit_status = 'RED'   # Default value
        if visit_date == date_controlled:
            if inat_observation.how_treated == 'Cut but roots remain':
                visit_status = 'ORANGE'
            elif inat_observation.treated == 'Yes':
                visit_status = 'YELLOW'
        elif visit_date == date_of_status_update:
            if inat_observation.status_update == 'Dead / Not Present':
                visit_status = 'GREEN'
            elif inat_observation.status_update == 'Duplicate':
                visit_status = 'GRAY'

        return visit_date, visit_status
