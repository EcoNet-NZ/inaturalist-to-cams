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
from inat_to_cams.username_cache import get_username_cache


class INatReader:
    # Centralized registry of observation fields processed by this project
    # MAINTAINER NOTE: When adding new observation fields to the project,
    # add them to this set to ensure they are included in RecordedBy tracking
    TRACKED_OBSERVATION_FIELDS = {
        # Current observation fields (from get_observation_value calls)
        'Location details',
        'Height (m)', 
        'Area in square meters',
        'Radius (m) of area surveyed',
        'Plant phenology->most common flowering/fruiting reproductive stage',
        'Effort to control',
        'Site difficulty', 
        'How treated',
        'Treated ?',
        'Status update',
        'Treatment substance',
        'Treatment details',
        'Date for next visit',
        
        # Current date observation fields (from get_date_observation_value calls)
        'Date controlled',
        'Date of status update',
        
        # Legacy fields (for backward compatibility)
        'Follow-up (YYYY-MM)',
        'Is the pest controlled?',
        'dead or alive?',
        'Adult Area',
        'area of infestation (m2)',
        'Professional assistance required',
        'fruiting',
        'Flowering',
    }
    
    @staticmethod
    def get_most_recent_field_update_info(observation):
        """Get the username and date of the most recent tracked observation field update
        
        This method finds the most recently updated observation field from the fields
        that this project processes (see TRACKED_OBSERVATION_FIELDS).
        
        If no tracked fields exist, falls back to:
        1. Last editor of the observation (user + updated_at)
        2. Creator of the observation (user + created_at)
        
        Returns:
            tuple: (username, datetime) or (None, None) if no info available
        """
        if not observation.ofvs:
            return INatReader._get_observation_fallback_info(observation)
        
        # Filter to only tracked observation fields
        tracked_ofvs = [ofv for ofv in observation.ofvs 
                       if ofv.name in INatReader.TRACKED_OBSERVATION_FIELDS]
        
        if not tracked_ofvs:
            logging.info(f"No tracked observation fields found for observation {observation.id}, using fallback")
            return INatReader._get_observation_fallback_info(observation)
        
        try:
            # Find the most recently updated tracked observation field
            # Use the field's own timestamp (when the field was updated)
            most_recent_ofv = max(tracked_ofvs, 
                                key=lambda x: getattr(x, 'updated_at', getattr(x, 'created_at', datetime.datetime.min)))
            
            # Get user information from the field
            username = None
            if hasattr(most_recent_ofv, 'user') and most_recent_ofv.user:
                username = getattr(most_recent_ofv.user, 'login', None)
                if not username:
                    username = getattr(most_recent_ofv.user, 'name', None)
            elif hasattr(most_recent_ofv, 'user_id') and most_recent_ofv.user_id:
                # Fallback: if we only have user_id, fetch username using cache
                cache = get_username_cache()
                username = cache.get_username(most_recent_ofv.user_id)
            
            # Get the timestamp when this specific field was updated
            update_date = getattr(most_recent_ofv, 'updated_at', getattr(most_recent_ofv, 'created_at', None))
            
            if username and update_date:
                logging.debug(f"Found most recent field update: {most_recent_ofv.name} by {username} at {update_date}")
                return username, update_date
            else:
                logging.warning(f"Could not extract user/date from field {most_recent_ofv.name}, using fallback")
                return INatReader._get_observation_fallback_info(observation)
                
        except Exception as e:
            logging.warning(f"Could not extract field update info: {e}")
            return INatReader._get_observation_fallback_info(observation)
    
    @staticmethod
    def _get_observation_fallback_info(observation):
        """Fallback: get observation editor/creator info when no tracked fields exist
        
        Priority:
        1. Last editor (user + updated_at) 
        2. Creator (user + created_at)
        
        Returns:
            tuple: (username, datetime) or (None, None) if no info available
        """
        username = None
        update_date = None
        
        # Try last editor first (updated_at)
        if hasattr(observation, 'updated_at') and observation.updated_at:
            if hasattr(observation, 'user') and observation.user:
                username = getattr(observation.user, 'login', None)
                if not username:
                    username = getattr(observation.user, 'name', None)
                if username:
                    update_date = observation.updated_at
                    logging.debug(f"Using observation last editor: {username} at {update_date}")
                    return username, update_date
        
        # Fallback to creator (created_at)
        if hasattr(observation, 'created_at') and observation.created_at:
            if hasattr(observation, 'user') and observation.user:
                username = getattr(observation.user, 'login', None)
                if not username:
                    username = getattr(observation.user, 'name', None)
                if username:
                    update_date = observation.created_at
                    logging.debug(f"Using observation creator: {username} at {update_date}")
                    return username, update_date
        
        logging.warning(f"Could not determine user info for observation {getattr(observation, 'id', 'unknown')}")
        return None, None

    @staticmethod
    def validate_tracked_fields():
        """Validation method to ensure all observation fields used in the code are tracked
        
        This method should be called during testing to ensure the TRACKED_OBSERVATION_FIELDS
        set includes all fields that are actually being processed by get_observation_value
        and get_date_observation_value calls.
        
        MAINTAINER NOTE: If this validation fails, you need to add the missing field(s)
        to TRACKED_OBSERVATION_FIELDS.
        
        Returns:
            tuple: (bool, set, set) - (is_complete, missing_fields, extra_fields)
        """
        # Fields that should be tracked based on current code usage
        expected_fields = {
            # From get_observation_value calls in flatten()
            'Location details', 'Height (m)', 'Area in square meters',
            'Radius (m) of area surveyed', 
            'Plant phenology->most common flowering/fruiting reproductive stage',
            'Effort to control', 'Site difficulty', 'How treated', 'Treated ?',
            'Status update', 'Treatment substance', 'Treatment details',
            'Date for next visit',
            
            # From get_date_observation_value calls in flatten()
            'Date controlled', 'Date of status update',
            
            # Legacy fields used in flatten()
            'Follow-up (YYYY-MM)', 'Is the pest controlled?', 'dead or alive?',
            'Adult Area', 'area of infestation (m2)', 
            'Professional assistance required', 'fruiting', 'Flowering'
        }
        
        tracked_fields = INatReader.TRACKED_OBSERVATION_FIELDS
        missing_fields = expected_fields - tracked_fields
        extra_fields = tracked_fields - expected_fields
        
        is_complete = len(missing_fields) == 0
        
        if missing_fields:
            logging.error(f"Missing fields in TRACKED_OBSERVATION_FIELDS: {missing_fields}")
        if extra_fields:
            logging.warning(f"Extra fields in TRACKED_OBSERVATION_FIELDS: {extra_fields}")
        if is_complete and not extra_fields:
            logging.info("All observation fields are properly tracked")
        
        return is_complete, missing_fields, extra_fields

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

        # Add the new fields for tracking updates
        inat_observation.recorded_by, inat_observation.recorded_date = INatReader.get_most_recent_field_update_info(observation)

        return inat_observation

    @staticmethod
    def get_observation_value(observation, key):
        # MAINTAINER NOTE: When adding a new field here, also add it to TRACKED_OBSERVATION_FIELDS
        # to ensure it's included in RecordedBy tracking
        if observation.ofvs:
            list_val = [x for x in observation.ofvs if x.name == key]
            if list_val:
                return list_val[0].value
        return None

    @staticmethod
    def get_date_observation_value(observation, key):
        # MAINTAINER NOTE: When adding a new date field here, also add it to TRACKED_OBSERVATION_FIELDS
        # to ensure it's included in RecordedBy tracking
        date = INatReader.get_observation_value(observation, key)
        if date:
            # Handle both datetime objects and string values
            if hasattr(date, 'isoformat'):
                formatted_date = date.isoformat()
            else:
                formatted_date = str(date)
            
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
    def get_project_observations_updated_since(place_ids, project_id, time_of_previous_update, not_taxon_ids=None):
        client = pyinaturalist.iNatClient()
        params = {
            'updated_since': time_of_previous_update + datetime.timedelta(seconds=1),
            'project_id': project_id,
            'place_id': place_ids,
            'geo': True,
            'geoprivacy': 'open',
            'page': 'all',
            'per_page': 200
        }

        # Add not_taxon_ids if provided
        if not_taxon_ids:
            params['without_taxon_id'] = not_taxon_ids

        observations = client.observations.search(**params).all()
        return observations

    @staticmethod
    @retry(delay=5, tries=3)
    def get_observation_with_id(observation_id):
        client = pyinaturalist.iNatClient()
        observation = client.observations(observation_id)
        if not observation:
            raise ValueError(f'Observation with id {observation_id} not found')
        return observation
