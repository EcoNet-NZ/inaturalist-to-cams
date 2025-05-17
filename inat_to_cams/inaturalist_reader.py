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

import pyinaturalist
import re

from retry import retry

from inat_to_cams import inaturalist_observation, exceptions
from inat_to_cams.translator import INatToCamsTranslator


class INatReader:
    @staticmethod
    def flatten(observation):
        if observation.location is None:
            logging.exception(f'Skipping observation {observation.id} since it has no location set')
            raise exceptions.InvalidObservationError

        date_observed = observation.observed_on
        if not date_observed:
            logging.info('No observation date found, using creation date instead')
            date_observed = observation.created_at

        if not date_observed:
            logging.warning(f'Skipping observation {observation.id} since it has no observation or creation date set')
            raise exceptions.InvalidObservationError

        if not observation.taxon:
            logging.warning(f'Skipping observation {observation.id} since it has no taxon associated with it')
            raise exceptions.InvalidObservationError
        
        inat_observation = inaturalist_observation.iNatObservation()
        inat_observation.id = observation.id
        inat_observation.location = inaturalist_observation.iNatPoint(observation.location[1], observation.location[0])
        inat_observation.location_accuracy = observation.positional_accuracy
        inat_observation.location_details = INatReader.get_observation_value(observation, 'Location details')
        inat_observation.taxon_lineage = observation.taxon.ancestor_ids
        
        # Add taxon name information for unmapped taxa
        if hasattr(observation.taxon, 'name'):
            inat_observation.taxon_name = observation.taxon.name
        if hasattr(observation.taxon, 'preferred_common_name'):
            inat_observation.taxon_preferred_common_name = observation.taxon.preferred_common_name
            
        inat_observation.description = observation.description
        inat_observation.quality_grade = observation.quality_grade
        inat_observation.height = INatReader.get_observation_value(observation, 'Height (m)')
        inat_observation.area = INatReader.get_observation_value(observation, 'Area in square meters')
        inat_observation.radius_surveyed = INatReader.get_observation_value(observation, 'Radius (m) of area surveyed')
        inat_observation.observed_on = date_observed.isoformat()[0:-6]
        if observation.photos:
            # Get the URLs and attribution
            photo_urls = []
            for i in range(min(5, len(observation.photos))):
                photo_url = observation.photos[i].url.replace("square.", "large.")
                photo_urls.append(photo_url)
            inat_observation.image_urls = ",".join(photo_urls)
            inat_observation.image_attribution = observation.photos[0].attribution

        inat_observation.phenology = INatReader.get_observation_value(observation, 'Plant phenology->most common flowering/fruiting reproductive stage')

        inat_observation.effort_to_control = INatReader.get_observation_value(observation, 'Effort to control')
        inat_observation.site_difficulty = INatReader.get_observation_value(observation, 'Site difficulty')

        inat_observation.date_controlled = INatReader.get_date_observation_value(observation, 'Date controlled')
        inat_observation.date_of_status_update = INatReader.get_date_observation_value(observation, 'Date of status update')
        inat_observation.how_treated = INatReader.get_observation_value(observation, 'How treated')
        inat_observation.treated = INatReader.get_observation_value(observation, 'Treated ?')
        inat_observation.status_update = INatReader.get_observation_value(observation, 'Status update')
        inat_observation.treatment_substance = INatReader.get_observation_value(observation, 'Treatment substance')
        inat_observation.treatment_details = INatReader.get_observation_value(observation, 'Treatment details')

        inat_observation.follow_up_date = INatReader.get_observation_value(observation, 'Date for next visit')

        # Legacy WMANZ observation fields
        if not inat_observation.follow_up_date:
            follow_up = INatReader.get_observation_value(observation, 'Follow-up (YYYY-MM)')
            if follow_up and follow_up != '(undef.)':
                inat_observation.follow_up_date = INatToCamsTranslator().as_local_datetime(follow_up + '-01')
            else:
                inat_observation.follow_up_date = None

        # Legacy OMB Wellington observation fields
        if not inat_observation.treated:
            controlled = INatReader.get_observation_value(observation, 'Is the pest controlled?')
            if controlled and controlled == 'yes':
                inat_observation.treated = 'Yes'
            if not inat_observation.treated:
                dead_or_alive = INatReader.get_observation_value(observation, 'dead or alive?')
                if dead_or_alive and dead_or_alive == 'dead':
                    inat_observation.treated = 'Yes'

        if not inat_observation.area:
            inat_observation.area = INatReader.get_observation_value(observation, 'Adult Area')
            if not inat_observation.area:
                inat_observation.area = INatReader.get_observation_value(observation, 'area of infestation (m2)')

        if not inat_observation.site_difficulty:
            professional_assistance = INatReader.get_observation_value(observation, 'Professional assistance required')
            if professional_assistance and professional_assistance == 'yes':
                inat_observation.site_difficulty = '5 Professional skills required (eg rope access)'

        if not inat_observation.phenology:
            fruiting = INatReader.get_observation_value(observation, 'fruiting')
            if fruiting and fruiting == 'yes':
                inat_observation.phenology = 'mature fruit'
            if not inat_observation.phenology:
                flowering = INatReader.get_observation_value(observation, 'Flowering')
                if flowering and flowering == 'yes':
                    inat_observation.phenology = 'flowers'

        return inat_observation

    @staticmethod
    def get_observation_value(observation, key):
        if observation.ofvs:
            list_val = [x for x in observation.ofvs if x.name == key]
            if list_val:
                return list_val[0].value
        return None

    @staticmethod
    def get_date_observation_value(observation, key):
        date = INatReader.get_observation_value(observation, key)
        if date:
            formatted_date = date.isoformat()
            timezone_pattern = re.compile(r'.*\+\d{2}:\d{2}')

            if timezone_pattern.match(formatted_date):
                return formatted_date[0:-6]
            else:
                return formatted_date

    @staticmethod
    @retry(delay=5, tries=3)
    def get_matching_observations_updated_since(place_ids, taxon_ids, time_of_previous_update):
        client = pyinaturalist.iNatClient()
        observations = client.observations.search(
            updated_since=time_of_previous_update + datetime.timedelta(seconds=1),
            taxon_id=taxon_ids,
            place_id=place_ids,
            geo=True,
            geoprivacy='open',
            page='all',
            per_page=200
        ).all()
        return observations

    @staticmethod
    @retry(delay=5, tries=3)
    def get_project_observations_updated_since(place_ids, project_id, time_of_previous_update):
        client = pyinaturalist.iNatClient()
        observations = client.observations.search(
            updated_since=time_of_previous_update + datetime.timedelta(seconds=1),
            project_id=project_id,
            place_id=place_ids,
            geo=True,
            geoprivacy='open',
            page='all',
            per_page=200
        ).all()
        return observations

    @staticmethod
    @retry(delay=5, tries=3)
    def get_observation_with_id(observation_id):
        client = pyinaturalist.iNatClient()
        observation = client.observations(observation_id)
        if not observation:
            raise ValueError(f'Observation with id {observation_id} not found')
        return observation
