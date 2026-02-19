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
import os

import arcgis
from retry import retry

from inat_to_cams import config, setup_logging


class CamsConnection:

    @retry(delay=5, tries=3)
    def __init__(self):
        print(f"Connecting to {os.environ['ARCGIS_URL']}")
        # self.gis = arcgis.GIS(profile='econet')
        self.gis = arcgis.GIS(url=os.environ['ARCGIS_URL'],
                              username=os.environ['ARCGIS_USERNAME'],
                              password=os.environ['ARCGIS_PASSWORD'])
        print("Connecting to layer")
        # self.gis = arcgis.GIS(profile='econet_sync')
        self.item = self.gis.content.get(os.environ['ARCGIS_FEATURE_LAYER_ID'])
        
        if self.item is None:
            raise ValueError(f"Could not find feature layer with ID '{os.environ['ARCGIS_FEATURE_LAYER_ID']}'. "
                           f"Please check the ARCGIS_FEATURE_LAYER_ID environment variable and ensure the user "
                           f"'{self.gis.properties.user.username}' has access to this layer.")
        
        print("Connected")

        setup_logging.SetupLogging()
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S', force=True)
        logging.info(f"Successfully logged in to {self.item.type} '{self.item.title}' as '{self.gis.properties.user.username}'")

        self.layer = self.item.layers[0]
        self.table = self.item.tables[0]

        expected_layer_name = 'WeedLocations'
        actual_layer_name = self.layer.properties.name
        assert actual_layer_name == expected_layer_name, f'Expected layer name to be {expected_layer_name} but found {actual_layer_name}'

        expected_table_name = 'Visits_Table'
        actual_table_name = self.table.properties.name
        assert actual_table_name == expected_table_name, f'Expected table name to be {expected_table_name} but found {actual_table_name}'

        self.test_schema = ['iNat_to_CAMS_Dev', 'XXX Nigel_Updated_EasyEditor_DEV - clone of CAMS Weeds (FL_BASE ALL)' ]

    def is_test_schema(self):
        return self.item.title in self.test_schema or 'clone of CAMS Weeds (FL_BASE ALL)' in self.item.title

    @retry(delay=5, tries=3)
    def query_weed_visits_table(self, query_table):
        return self.table.query(where=query_table, order_by_fields='OBJECTID')

    @retry(delay=5, tries=3)
    def query_weed_visits_table_ids(self, query_table):
        return self.table.query(where=query_table, order_by_fields='OBJECTID', returnIdsOnly=True)

    @retry(delay=5, tries=3)
    def query_weed_location_layer(self, query_layer):
        return self.layer.query(where=query_layer)

    @retry(delay=5, tries=3)
    def query_weed_location_layer_limit_records(self, query_layer, max_record_count):
        return self.layer.query(where=query_layer, result_record_count=max_record_count, return_all_records=False)

    @retry(delay=5, tries=3)
    def query_weed_location_layer_wgs84(self, query_layer):
        results = self.layer.query(where=query_layer, out_sr=4326)
        #logging.info(f"Found Location Layer sgs84 {results}")
        return results

    @retry(delay=5, tries=3)
    def add_weed_location_layer_row(self, new_layer_row):
        results = self.layer.edit_features(adds=new_layer_row)
        assert len(results['addResults']) == 1
        assert results['addResults'][0]['success'], f"Error writing WeedLocation {results['addResults'][0]}"
        return results['addResults'][0]['globalId'], results['addResults'][0]['objectId']

    @retry(delay=5, tries=3)
    def update_weed_location_layer_row(self, new_layer_row):
        results = self.layer.edit_features(updates=new_layer_row)
        assert len(results['updateResults']) == 1
        assert results['updateResults'][0]['success'], f"Error writing WeedLocation {results['updateResults'][0]}"

    def delete_visit_rows_with_object_id_gt(self, object_id):
        query = f"OBJECTID > {object_id}"
        self.delete_table_rows_if_allowed(query)


    @retry(delay=5, tries=3)
    def delete_table_rows_if_allowed(self, query):
        logging.info(f'Deleting table rows where {query}')
        if self.is_test_schema():
            self.table.delete_features(where=query)
            logging.info(f"Deleted table rows where {query}")
        else:
            logging.info(f"ERROR: for safety, records can only be deleted from test schemas. Current schema: '{self.item.title}'")
            exit(1)

    def delete_location_rows_with_object_id_gt(self, object_id):
        query = f"OBJECTID > {object_id}"
        self.delete_layer_rows_if_allowed(query)

    @retry(delay=5, tries=3)
    def delete_layer_rows_if_allowed(self, query):
        logging.info(f'Deleting layer rows where {query}')
        if self.is_test_schema():
            self.layer.delete_features(where=query)
            logging.info(f"Deleted layer rows where {query}")
        else:
            logging.info(f"ERROR: for safety, records can only be deleted from test schemas. Current schema: '{self.item.title}'")
            exit(1)

    def delete_feature_with_id(self, inat_id):
        logging.info(f'Deleting features with iNat id {inat_id}')
        query_table = f"iNatRef='{inat_id}'"
        rows = self.query_weed_visits_table(query_table)
        if rows:
            table_rows_deleted = self.delete_table_rows(rows)
            features_deleted = self.delete_features(rows)
            logging.info(f'{table_rows_deleted} table rows and {features_deleted} features deleted')
        else:
            logging.info('0 features deleted')

    def delete_rows_with_inat_ref_of_length(self, length):
        logging.info(f'Deleting features where the length of iNatRef is {length}')
        query_table = f"CHAR_LENGTH(TRIM(TRAILING ' ' FROM iNatRef))={length}"
        rows = self.query_weed_visits_table(query_table)
        if rows:
            table_rows_deleted = self.delete_table_rows(rows)
            features_deleted = self.delete_features(rows)
            logging.info(f'{table_rows_deleted} table rows and {features_deleted} features deleted')
        else:
            logging.info('0 features deleted')

    def delete_features(self, rows):
        global_ids = [row.attributes['GUID_visits'] for row in rows]
        unique_global_ids = list(dict.fromkeys(global_ids))
        query_feature_rows = f"GlobalID IN ({str(unique_global_ids).replace('[', '').replace(']', '')})"
        logging.info(f'Deleting feature rows with {query_feature_rows}')
        self.delete_layer_rows_if_allowed(query_feature_rows)
        return len(unique_global_ids)

    def delete_table_rows(self, rows):
        # As an alternative, could set up a composite relationship, see https://community.esri.com/t5/arcgis-online-questions/delete-record-in-related-table-when-parent-feature/td-p/1127320
        inat_refs = [row.attributes['iNatRef'] for row in rows]
        query_table_rows = f"iNatRef IN ({str(inat_refs).replace('[', '').replace(']', '')})"
        logging.info(f'Deleting table rows with {query_table_rows}')
        self.delete_table_rows_if_allowed(query_table_rows)
        return len(inat_refs)

    @retry(delay=5, tries=3)
    def visits_row_count(self, inat_id):
        query = f"iNatRef='{inat_id}'"
        row_count = self.table.query(where=query, return_count_only=True)
        return row_count

    def visits_row(self, inat_id, index=0):
        query = f"iNatRef='{inat_id}'"
        row = self.query_weed_visits_table(query)
        # logging.info (self.cams.table.properties.name)
        # for field in self.cams.table.properties.fields:
        #     logging.info(f"{field['name']:30}{field['type']}")
        logging.info(f'Reading visits row {row.features[index].attributes}')
        return row.features[index].attributes

    @retry(delay=5, tries=3)
    def visits_row_count_with_same_locations_feature_as_visits_row(self, inat_id):
        query = f"iNatRef='{inat_id}'"
        row = self.query_weed_visits_table(query)
        logging.info(f'Reading visits row {row.features[0].attributes}')
        global_id = row.features[0].attributes['GUID_visits']
        logging.info(f'Global id {global_id}')
        return self.table.query(where=f"GUID_visits='{global_id}'", return_count_only=True)

    @retry(delay=5, tries=3)
    def get_feature_global_id(self, inat_id):
        query = f"iNatRef='{inat_id}'"
        row = self.query_weed_visits_table(query)
        return row.features[0].attributes['GUID_visits']

    def get_location(self, global_id):
        query = f"globalId='{global_id}'"
        feature_set = self.query_weed_location_layer(query)
        logging.info(f'Getting location {feature_set.features[0].geometry}')
        return feature_set.features[0].geometry
    
    def get_location_wgs84(self, global_id):
        query = f"globalId='{global_id}'"
        feature_set = self.query_weed_location_layer_wgs84(query)
        logging.info(f'Getting location {feature_set.features[0].geometry}')
        return feature_set.features[0].geometry
    
    def get_location_details(self, global_id):
        query = f"globalId='{global_id}'"
        feature_set = self.query_weed_location_layer(query)
        logging.info(f'Getting location details {feature_set.features[0].attributes}')
        return feature_set.features[0].attributes


class CamsSchemaComparator:
    def compare(self, schema_entity):
        if schema_entity == 'WeedLocations':
            cams_entity = connection.layer
        elif schema_entity == 'Visits_Table':
            cams_entity = connection.table
        else:
            raise ValueError(f'schema_entity {schema_entity} not known')

        for key in config.cams_schema[schema_entity]:
            schema_field = config.cams_schema[schema_entity][key]
            expected_name = schema_field['name']
            expected_type = f"esriFieldType{schema_field['type']}"
            expected_values = ''
            if expected_name == 'SpeciesDropDown':
                expected_values = config.taxon_mapping.values()
            elif 'values' in schema_field:
                expected_values = list(schema_field['values'].values())

            fields = [x for x in cams_entity.properties.fields if x.name == expected_name]
            assert len(fields) == 1, \
                f"Expected CAMS '{schema_entity}' schema to have a field with name '{expected_name}'"
            actual_field = fields[0]

            assert actual_field['type'] == expected_type, \
                f"Expected CAMS '{schema_entity}' field '{schema_field['name']}' to have type '{expected_type}' but found type '{actual_field['type']}'"

            if expected_type == 'esriFieldTypeString':
                expected_length = schema_field['length']
                assert actual_field['length'] == expected_length, \
                    f"Expected CAMS '{schema_entity}' field '{schema_field['name']}' to have length '{expected_length}' but found length '{actual_field['length']}'"

            actual_values = ""
            if actual_field['domain'] and 'codedValues' in actual_field['domain']:
                coded_values = actual_field['domain']['codedValues']
                actual_values = list(map(lambda x: x['code'], coded_values))

            assert set(expected_values).issubset(set(actual_values)), \
                f"Expected CAMS '{schema_entity}' field '{schema_field['name']}' to include values '{expected_values}' but found values '{actual_values}'"

        logging.info(f"Actual '{schema_entity}' schema matches expected schema")


connection = CamsConnection()
