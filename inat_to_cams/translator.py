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
from pyinaturalist import get_user_by_id

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
    
    def translate(self, inat_observation, original_observation):
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

        (visit_date, visit_status, recorded_by_user_id, recorded_by_username) = self.calculate_visit_date_and_status_and_user(inat_observation, original_observation)

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
        # Validate and normalize follow_up_date
        if inat_observation.follow_up_date:
            # Handle both datetime objects and strings
            if hasattr(inat_observation.follow_up_date, 'isoformat'):
                follow_up_datetime = inat_observation.follow_up_date
            else:
                follow_up_datetime = self.as_local_datetime(inat_observation.follow_up_date)
            
            # Check if follow_up_date is after the visit date
            if follow_up_datetime and weed_visit.date_visit_made:
                if follow_up_datetime <= weed_visit.date_visit_made:
                    logging.info(f'Ignoring follow-up date {follow_up_datetime} as it is before or on visit date {weed_visit.date_visit_made}')
                    weed_visit.follow_up_date = None
                else:
                    weed_visit.follow_up_date = follow_up_datetime
            else:
                weed_visit.follow_up_date = follow_up_datetime
        else:
            weed_visit.follow_up_date = None
        
        weed_visit.phenology = inat_observation.phenology
        weed_visit.visit_status = visit_status
        weed_visit.treated = inat_observation.treated
        weed_visit.how_treated = inat_observation.how_treated
        weed_visit.treatment_substance = inat_observation.treatment_substance
        if weed_visit.treatment_substance == 'None':
            weed_visit.treatment_substance = None
        weed_visit.treatment_details = inat_observation.treatment_details
        
        # Add new fields for tracking updates
        # Store both user_id and username as strings in CAMS
        weed_visit.recorded_by_user_id = str(recorded_by_user_id) if recorded_by_user_id else None
        weed_visit.recorded_by_username = recorded_by_username
        if inat_observation.recorded_date:
            if hasattr(inat_observation.recorded_date, 'isoformat'):
                # It's a datetime object
                weed_visit.recorded_date = self.as_local_datetime(inat_observation.recorded_date.isoformat())
            else:
                # It's already a string
                weed_visit.recorded_date = self.as_local_datetime(str(inat_observation.recorded_date))
        else:
            weed_visit.recorded_date = None

        return cams_feature.CamsFeature(geolocation, weed_location, weed_visit)

    def as_local_datetime(self, date_field):
        if not date_field:
            return None
        timestamp = datetime.fromisoformat(date_field)
        naive_datetime = timestamp.replace(tzinfo=None)
        assert naive_datetime.tzinfo is None
        return naive_datetime

    @staticmethod
    def _get_attr(obj, attr_name, default=None):
        """Helper to get attribute from either dict or object"""
        if isinstance(obj, dict):
            return obj.get(attr_name, default)
        else:
            return getattr(obj, attr_name, default)
    
    def _get_user_id_from_item(self, item, context=""):
        """Extract user_id from an OFV or observation, prioritizing updater_id over user_id"""
        # Try updater_id first
        updater_id = self._get_attr(item, 'updater_id')
        if updater_id:
            logging.debug(f"Using {context}updater_id: {updater_id}")
            return updater_id
        
        # Try updater.id
        updater = self._get_attr(item, 'updater')
        if updater:
            updater_id = self._get_attr(updater, 'id')
            if updater_id:
                logging.debug(f"Using {context}updater.id: {updater_id}")
                return updater_id
        
        # Try user_id
        user_id = self._get_attr(item, 'user_id')
        if user_id:
            logging.debug(f"Using {context}user_id: {user_id}")
            return user_id
        
        # Try user.id
        user = self._get_attr(item, 'user')
        if user:
            user_id = self._get_attr(user, 'id')
            if user_id:
                logging.debug(f"Using {context}user.id: {user_id}")
                return user_id
        
        return None
    
    def _get_username_for_user_id(self, user_id, original_observation):
        """Find username for a given user_id by scanning OFVs and observation"""
        ofvs = self._get_attr(original_observation, 'ofvs')
        
        # Scan OFVs to find one where user_id matches (user object refers to user_id, not updater_id)
        if ofvs:
            for ofv in ofvs:
                ofv_user_id = self._get_attr(ofv, 'user_id')
                if ofv_user_id == user_id:
                    user = self._get_attr(ofv, 'user')
                    if user:
                        login = self._get_attr(user, 'login')
                        if login:
                            logging.debug(f"Found username for user_id {user_id}: {login}")
                            return login
        
        # Check observation-level updater
        updater = self._get_attr(original_observation, 'updater')
        if updater and self._get_attr(updater, 'id') == user_id:
            login = self._get_attr(updater, 'login')
            if login:
                logging.debug(f"Using observation updater username: {login}")
                return login
        
        # Check observation-level user
        user = self._get_attr(original_observation, 'user')
        if user and self._get_attr(user, 'id') == user_id:
            login = self._get_attr(user, 'login')
            if login:
                logging.debug(f"Using observation username: {login}")
                return login
        
        # Final fallback: fetch from API
        try:
            user_data = get_user_by_id(user_id)
            if user_data and 'login' in user_data:
                username = user_data['login']
                logging.debug(f"Fetched username from API for user_id {user_id}: {username}")
                return username
        except Exception as e:
            logging.warning(f"Failed to fetch username for user_id {user_id}: {e}")
        
        return None
    
    def calculate_visit_date_and_status_and_user(self, inat_observation, original_observation):
        date_first_observed = inat_observation.observed_on
        date_controlled = inat_observation.date_controlled
        date_of_status_update = inat_observation.date_of_status_update
        
        logging.info(f'DEBUG calculate_visit_date: date_first_observed={date_first_observed}, date_controlled={date_controlled}, date_of_status_update={date_of_status_update}')

        # Determine which date to use (existing logic)
        if date_controlled and date_of_status_update:
            if date_controlled > date_of_status_update:
                visit_date = date_controlled
                winning_field = 'Date controlled'
            else:
                visit_date = date_of_status_update
                winning_field = 'Date of status update'
        elif date_controlled:
            visit_date = date_controlled
            winning_field = 'Date controlled'
        elif date_of_status_update:
            visit_date = date_of_status_update
            winning_field = 'Date of status update'
        else:
            visit_date = date_first_observed
            winning_field = None

        # Determine visit status (existing logic)
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

        # Determine user_id from the winning field
        # TODO: The updater is not returned by the iNatClient observation we are using, we need to find another way to read the observations
        recorded_by_user_id = None
        # ofvs = self._get_attr(original_observation, 'ofvs')
        
        # if winning_field and ofvs:
        #     # Find the observation field value for the winning field
        #     for ofv in ofvs:
        #         ofv_name = self._get_attr(ofv, 'name')
        #         ofv_value = self._get_attr(ofv, 'value')
        #         if ofv_name == winning_field and ofv_value:
        #             recorded_by_user_id = self._get_user_id_from_item(ofv, f"{winning_field} field ")
        #             break
        
        # # Fallback to observation-level user if no winning field found
        # if not recorded_by_user_id:
        #     recorded_by_user_id = self._get_user_id_from_item(original_observation, "observation ")

        # Get the username for the recorded_by_user_id
        recorded_by_username = None
        # if recorded_by_user_id:
        #     recorded_by_username = self._get_username_for_user_id(recorded_by_user_id, original_observation)

        logging.info(f'DEBUG calculate_visit_date result: visit_date={visit_date}, visit_status={visit_status}')
        return visit_date, visit_status, recorded_by_user_id, recorded_by_username
