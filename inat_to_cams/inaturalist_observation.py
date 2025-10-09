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

class iNatPoint:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return f"{self.x},{self.y}"


class iNatObservation:
    def __init__(self):
        self.id = None
        self.location = None
        self.location_accuracy = None
        self.location_details = None
        self.description = None
        self.quality_grade = None
        self.height = None
        self.area = None
        self.radius_surveyed = None
        self.observed_on = None
        self.taxon_lineage = None
        self.taxon_name = None
        self.taxon_preferred_common_name = None
        self.phenology = None
        self.image_urls = None
        self.image_attribution = None

        self.effort_to_control = None
        self.site_difficulty = None
        self.follow_up_date = None

        self.treated = None
        self.how_treated = None
        self.treatment_substance = None
        self.treatment_details = None
        self.date_controlled = None

        self.status_update = None
        self.date_of_status_update = None
        
        # New fields for tracking updates
        self.recorded_by = None  # Username (not user_id)
        self.recorded_date = None  # DateTime with time component