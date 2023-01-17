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


def normalise_geolocation(geo_dict):
    geo_dict['geolocation']['spatialReference'].pop('latestWkid', None)
    geo_dict['geolocation']['x'] = round(geo_dict['geolocation']['x'], 6)
    geo_dict['geolocation']['y'] = round(geo_dict['geolocation']['y'], 6)


class CamsFeature:

    def __init__(self, geolocation, weed_location, weed_visits):
        self.geolocation = geolocation
        self.weed_location = weed_location
        self.weed_visits = weed_visits

    def __eq__(self, other):
        if type(other) is type(self):
            self_dict = self.__dict__
            other_dict = other.__dict__
            normalise_geolocation(self_dict)
            normalise_geolocation(other_dict)
            return self_dict == other_dict
        return False

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self.__dict__)


class WeedLocation:

    def __init__(self):
        self.object_id = None
        self.global_id = None
        self.date_first_observed = None
        self.species = None
        self.data_source = None
        self.location_details = None
        self.effort_to_control = None
        self.current_status = None
        self.external_url = None

    def __eq__(self, other):
        if type(other) is type(self):
            ignore_keys = ['object_id', 'global_id']
            ka = set(self.__dict__).difference(ignore_keys)
            kb = set(other.__dict__).difference(ignore_keys)
            return ka == kb and all(self.__dict__[k] == other.__dict__[k] for k in ka)
        return False

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self.__dict__)


class WeedVisit:

    def __init__(self):
        self.object_id = None
        self.height = None
        self.area = None
        self.radius_surveyed = None
        self.observation_quality = None
        self.site_difficulty = None
        self.date_visit_made = None
        self.follow_up_date = None
        self.phenology = None
        self.visit_status = None

        self.treated = None
        self.how_treated = None
        self.treatment_substance = None
        self.treatment_details = None

        self.external_id = None
        self.external_url = None
        self.notes = None

    def __eq__(self, other):
        if type(other) is type(self):
            ignore_keys = ['object_id']
            ka = set(self.__dict__).difference(ignore_keys)
            kb = set(other.__dict__).difference(ignore_keys)
            return ka == kb and all(self.__dict__[k] == other.__dict__[k] for k in ka)
        return False

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self.__dict__)
