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

import json
import logging


class TaxonMappingConfiguration:

    def __init__(self):
        taxon_file = open('config/taxon_mapping.json')
        self.taxon_mapping = json.load(taxon_file)
        logging.info(f'Loaded taxon mapping: {self.taxon_mapping}')


class CamsSchemaConfiguration:
    def __init__(self):
        cams_schema_file = open('config/cams_schema.json')
        self.cams_schema = json.load(cams_schema_file)
        logging.info(f'Loaded CAMS schema: {self.cams_schema}')

    def cams_field_name(self, entity, field):
        return self.cams_schema[entity][field]['name']

    def cams_field_value(self, entity, field, key):
        if key:
            return self.cams_schema[entity][field]['values'][key]
        return None

    def cams_field_key(self, entity, field, value):
        if value:
            try:
                field_dict = self.cams_schema[entity][field]['values']
                return list(field_dict.keys())[list(field_dict.values()).index(value)]
            except ValueError:
                field_dict = self.cams_schema[entity][field]['legacy_values']
                return list(field_dict.keys())[list(field_dict.values()).index(value)]
        return None


class SyncConfiguration:
    def __init__(self):
        configuration_json = 'config/sync_configuration.json'
        sync_configuration_file = open(configuration_json)
        self.sync_configuration = json.load(sync_configuration_file)
        for key, value in self.sync_configuration.items():
            for name in ['file_prefix', 'place_ids']:
                assert name in value, (
                    f"'{name}' must be set for '{key}' in sync_configuration.json")
            
            # Either taxon_ids or project_id must be present, but not both
            has_taxon_ids = 'taxon_ids' in value
            has_project_id = 'project_id' in value
            
            assert has_taxon_ids or has_project_id, (
                f"Either 'taxon_ids' or 'project_id' must be set for '{key}' in "
                f"sync_configuration.json")
            assert not (has_taxon_ids and has_project_id), (
                f"Both 'taxon_ids' and 'project_id' cannot be set for '{key}' in "
                f"sync_configuration.json")

            # For taxon-based configs, check that all taxon IDs are mapped
            if has_taxon_ids:
                for taxon_id in value['taxon_ids']:
                    assert taxon_id in taxon_mapping, (
                        f"Taxon id {taxon_id} must be mapped in taxon_mapping.json")

        logging.info(f'Loaded sync configuration: {self.sync_configuration}')


cams_schema_config = CamsSchemaConfiguration()
cams_schema = cams_schema_config.cams_schema
taxon_mapping = TaxonMappingConfiguration().taxon_mapping
sync_configuration = SyncConfiguration().sync_configuration
