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

from datetime import date, datetime
import logging
import pytz

from arcgis import geometry

from inat_to_cams import cams_observation, config, exceptions


class INatToCamsTranslator:
    def translate(self, inat_observation):
        geolocation = geometry.Point({'x': inat_observation.location.x,
                                      'y': inat_observation.location.y,
                                      'spatialReference': {'wkid': 4326}
                                      })

        for taxon in reversed(inat_observation.taxon_lineage):
            cams_taxon = config.taxon_mapping.get(str(taxon))
            if cams_taxon is not None:
                break

        if cams_taxon is None:
            logging.exception(f'Skipping observation {inat_observation.id} since it has unmapped taxon with lineage {inat_observation.taxon_lineage}')
            raise exceptions.InvalidObservationError

        (visit_date, visit_status) = self.calculate_visit_date_and_status(inat_observation)

        weed_location = cams_observation.WeedLocation()
        weed_location.date_first_observed = self.as_local_datetime(inat_observation.observed_on)
        weed_location.species = cams_taxon
        weed_location.data_source = 'iNaturalist'
        weed_location.location_details = inat_observation.location_details
        effort_to_control = inat_observation.effort_to_control
        if effort_to_control:
            effort_to_control = int(effort_to_control[:1])
        else:
            effort_to_control = 1   # Default to 1

        weed_location.effort_to_control = effort_to_control
        weed_location.current_status = visit_status

        weed_visit = cams_observation.WeedVisit()
        weed_visit.external_id = str(inat_observation.id)
        weed_visit.external_url = f'https://www.inaturalist.org/observations/{inat_observation.id}'
        weed_visit.notes = inat_observation.description
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

        weed_visits = [weed_visit]

        cams_feature = cams_observation.CamsFeature(geolocation, weed_location, weed_visits)
        return cams_feature

    def as_local_datetime(self, date_field):
        return pytz.timezone('Pacific/Auckland').localize(datetime.fromisoformat(date_field))

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

        today = date.today()
        if today.month >= 7:
            year = today.year
        else:
            year = today.year - 1
        start_of_this_weed_year = str(year) + '-07-01T00:00:00'

        visit_status = 'RED'   # Default value
        if visit_date < start_of_this_weed_year:
            visit_status = 'PURPLE'
        elif visit_date == date_controlled:
            if inat_observation.how_treated == 'Cut but roots remain':
                visit_status = 'ORANGE'
            elif inat_observation.treated == 'Yes':
                visit_status = 'YELLOW'
        elif visit_date == date_of_status_update:
            if inat_observation.status_update == 'Dead / Not Present':
                visit_status = 'GREEN'

        return visit_date, visit_status
