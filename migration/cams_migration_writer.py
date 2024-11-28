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
from inat_to_cams import cams_interface, config


class CamsMigrationWriter:
    def __init__(self):
        self.cams = cams_interface.connection

    def write_new_feature_fields(self, cams_feature):
        logging.info(f'Updating CAMS iNaturalist Location {cams_feature.weed_location.external_url}')
        new_layer_row = [{            
            'attributes': {
            }
        }]
        fields = [
            ('Image URLs', cams_feature.weed_location.image_urls),
            ('Image Attribution', cams_feature.weed_location.image_attribution),
            ('Location Accuracy', cams_feature.weed_location.location_accuracy)
        ]

        [self.add_field(new_layer_row[0], 'WeedLocations', field) for field in fields]

        object_id = cams_feature.weed_location.object_id
        new_layer_row[0]['attributes']['objectId'] = object_id
        logging.info(f'Updating CAMS WeedLocations layer: {new_layer_row}')
        cams_interface.connection.update_weed_location_layer_row(new_layer_row)

        return

    def get_entry(self, table_name, field_name, field_value):
        cams_schema_config = config.cams_schema_config

        schema_field = cams_schema_config.cams_schema[table_name][field_name]
        if 'values' in schema_field:
            value = cams_schema_config.cams_field_value(table_name, field_name, field_value)
        else:
            value = field_value

        value = self.truncate_string_value_if_needed(schema_field, value)

        return (
            cams_schema_config.cams_field_name(table_name, field_name),
            value
        )

    def truncate_string_value_if_needed(self, schema_field, value):
        if value and schema_field['type'] == 'String' and len(value) > schema_field['length']:
            value = value[:schema_field['length'] - 3] + '...'
        return value

    def add_field(self, row, table_name, field):
        entry = self.get_entry(table_name, field[0], field[1])
        row['attributes'][entry[0]] = entry[1]
