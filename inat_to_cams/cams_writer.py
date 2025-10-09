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
from inat_to_cams import cams_interface, cams_reader, config, summary_logger


class CamsWriter:
    def __init__(self):
        self.cams = cams_interface.connection

    def write_observation(self, cams_feature, dry_run=False):
        reader = cams_reader.CamsReader()
        inat_id = cams_feature.latest_weed_visit.external_id
        existing_feature = reader.read_observation(inat_id)

        # Check if the latest visit record was created in CAMS. If so, we shouldn't update the visit record.
        update_visit_record = True
        if existing_feature:
            # Check for status rollover in audit_log
            rollover_date = None
            # Check the feature attributes for the Audit_Log field
            if hasattr(existing_feature.weed_location, 'audit_log') and existing_feature.weed_location.audit_log:
                try:
                    # Extract the first 10 characters from audit_log (YYYY-MM-DD format)
                    date_str = existing_feature.weed_location.audit_log[:10]
                    # Parse the date string into a datetime object
                    rollover_date = datetime.strptime(date_str, '%Y-%m-%d')
                    logging.info(f'Found rollover date in audit_log: {rollover_date}')
                except Exception as e:
                    logging.info(f'Could not parse rollover date from audit_log: {e}')
            
            # Check if either the existing CAMS visit date or the rollover date is more recent than the iNat visit date
            if existing_feature.latest_weed_visit.date_visit_made > cams_feature.latest_weed_visit.date_visit_made or \
               (rollover_date is not None and rollover_date > cams_feature.latest_weed_visit.date_visit_made):
                logging.info(f'Preserving CAMS status - visit date: {existing_feature.latest_weed_visit.date_visit_made}, rollover date: {rollover_date}, iNat date: {cams_feature.latest_weed_visit.date_visit_made}')
                # Preserve the existing status and effort_to_control values
                cams_feature.weed_location.current_status = existing_feature.weed_location.current_status
                cams_feature.weed_location.effort_to_control = existing_feature.weed_location.effort_to_control
                # Also preserve the audit_log
                cams_feature.weed_location.audit_log = existing_feature.weed_location.audit_log
                update_visit_record = False

            if existing_feature == cams_feature:
                logging.info('No relevant updates to observation')
                return

            #weed_geolocation_modified = existing_feature.geolocation != cams_feature.geolocation
            weed_geolocation_modified = (existing_feature.weed_location.iNaturalist_latitude != cams_feature.weed_location.iNaturalist_latitude) or (existing_feature.weed_location.iNaturalist_longitude != cams_feature.weed_location.iNaturalist_longitude)

            weed_location_modified = existing_feature.weed_location != cams_feature.weed_location
            weed_visit_modified = existing_feature.latest_weed_visit != cams_feature.latest_weed_visit and update_visit_record
            logging.info('Updating existing feature')
            logging.info(f'Weed geolocation modified? : {weed_geolocation_modified}')
            logging.info(f'Weed location modified? : {weed_location_modified}')
            logging.info(f'Weed visit modified? : {weed_visit_modified}')
        else:
            logging.info('Creating new feature')
            weed_geolocation_modified = True
            weed_location_modified = True
            weed_visit_modified = True

        feature_written = False
        if weed_geolocation_modified or weed_location_modified:
            global_id, object_id = self.write_feature(cams_feature, inat_id, existing_feature, dry_run, weed_geolocation_modified)
            feature_written = True
        else:
            global_id = existing_feature.weed_location.global_id
            object_id = existing_feature.weed_location.object_id

        if weed_visit_modified and update_visit_record:
            new_weed_visit_record = self.write_weed_visit(cams_feature, existing_feature, global_id, object_id, dry_run)

            if not feature_written:
                # write the feature as well as the visit so we don't have to wait for the visit status to be synced to the parent weed instance (currently via a webhook)
                self.write_feature(cams_feature, inat_id, existing_feature, dry_run, weed_geolocation_modified)  
        else:
            new_weed_visit_record = False

        self.write_summary_log(cams_feature, existing_feature, object_id, new_weed_visit_record, weed_geolocation_modified, weed_location_modified, weed_visit_modified)

        return global_id

    def write_summary_log(self, cams_feature, existing_feature, object_id, new_weed_visit_record, weed_geolocation_modified, weed_location_modified, weed_visit_modified):
        if not summary_logger.log_header_written:
            summary_logger.write_log_header()
            summary_logger.log_header_written = True
        if not summary_logger.config_name:
            summary_logger.write_config_name()
            summary_logger.config_name_written = True
        summary_logger.write_summary_log(cams_feature, object_id, existing_feature, new_weed_visit_record, weed_geolocation_modified, weed_location_modified, weed_visit_modified)

    def write_weed_visit(self, cams_feature, existing_feature, global_id, object_id, dry_run):
        weed_visit = cams_feature.latest_weed_visit
        new_data = [{
            'attributes': {
            }
        }]

        fields = [
            ('id', weed_visit.external_id),
            ('url', weed_visit.external_url),
            ('Date Visit Made', weed_visit.date_visit_made),
            ('Area m2', weed_visit.area),
            ('Height', weed_visit.height),
            ('Radius (m) of area surveyed', weed_visit.radius_surveyed),
            ('Site difficulty', weed_visit.site_difficulty),
            ('Date for next visit', weed_visit.follow_up_date),
            ('Plant phenology->most common flowering/fruiting reproductive stage', weed_visit.phenology),
            ('Treated', weed_visit.treated),
            ('How treated', weed_visit.how_treated),
            ('Treatment substance', weed_visit.treatment_substance),
            ('Treatment details', weed_visit.treatment_details),
            ('WeedVisitStatus', weed_visit.visit_status),
            ('ObservationQuality', weed_visit.observation_quality),
            ('description', weed_visit.notes),
            ('GUID_visits', global_id),
            ('RecordedBy', weed_visit.recorded_by),
            ('RecordedDate', weed_visit.recorded_date)
        ]

        [self.add_field(new_data[0], 'Visits_Table', field) for field in fields]

        new_weed_visit_record = True
        # Determine whether to create a new visit record if controlled or updated after previous visit
        if existing_feature:
            logging.info(f'New weed visit date: {weed_visit.date_visit_made}')
            logging.info(f'Existing weed visit date: {existing_feature.latest_weed_visit.date_visit_made}')
            logging.info(f'Dates equal? {weed_visit.date_visit_made == existing_feature.latest_weed_visit.date_visit_made}')
            if weed_visit.date_visit_made == existing_feature.latest_weed_visit.date_visit_made:
                new_weed_visit_record = False

        if not dry_run:
            if new_weed_visit_record:
                logging.info(f'Adding CAMS Weed_Visits table row: {new_data}')
                results = self.cams.table.edit_features(adds=new_data)
                assert len(results['addResults']) == 1
                assert results['addResults'][0]['success'], f"Error writing WeedVisits {results['addResults'][0]}"
            else:
                logging.info(f'Updating CAMS Weed_Visits table row: {new_data}')
                new_data[0]['attributes']['objectId'] = existing_feature.latest_weed_visit.object_id
                results = self.cams.table.edit_features(updates=new_data)
                assert len(results['updateResults']) == 1
                assert results['updateResults'][0]['success'], f"Error writing WeedVisits {results['updateResults'][0]}"
        return new_weed_visit_record

    def write_feature(self, cams_feature, inat_id, existing_feature, dry_run, write_geolocation):
        global_id = None
        logging.info(f'Writing feature to CAMS with iNaturalist id {inat_id} geometry: {cams_feature.geolocation}')
        new_layer_row = [{            
            'attributes': {
            }
        }]
        fields = [
            ('Date First Observed', cams_feature.weed_location.date_first_observed),
            ('Species', cams_feature.weed_location.species),
            ('DataSource', cams_feature.weed_location.data_source),
            ('Location details', cams_feature.weed_location.location_details),          
            ('Effort to control', cams_feature.weed_location.effort_to_control),
            ('CurrentStatus', cams_feature.weed_location.current_status),
            ('iNaturalistURL', cams_feature.weed_location.external_url),
            ('Image URLs', cams_feature.weed_location.image_urls),
            ('Image Attribution', cams_feature.weed_location.image_attribution),
            ('Location Accuracy', cams_feature.weed_location.location_accuracy)
        ]
        
        if cams_feature.weed_location.other_weed_details:
            fields.append(('Other Weed Details', cams_feature.weed_location.other_weed_details))
            
        if write_geolocation:
            fields.append(('iNaturalist Longitude', cams_feature.weed_location.iNaturalist_longitude))
            fields.append(('iNaturalist Latitude', cams_feature.weed_location.iNaturalist_latitude))
            new_layer_row[0]['geometry']=cams_feature.geolocation           
            logging.info(f'Weed geolocation has been modified in iNaturalist')

        if not existing_feature:
            fields.append(('GeoPrivacy', 'Open'))
            fields.append(('LandOwnership', 'NotAvailable'))

        [self.add_field(new_layer_row[0], 'WeedLocations', field) for field in fields]
        if not dry_run:
            if existing_feature:
                global_id = existing_feature.weed_location.global_id
                object_id = existing_feature.weed_location.object_id
                new_layer_row[0]['attributes']['objectId'] = object_id
                logging.info(f'Updating CAMS WeedLocations layer: {new_layer_row}')
                cams_interface.connection.update_weed_location_layer_row(new_layer_row)
            else:
                logging.info(f'Adding CAMS WeedLocations layer: {new_layer_row}')
                global_id, object_id = cams_interface.connection.add_weed_location_layer_row(new_layer_row)
        return global_id, object_id

    def get_observation_value(self, observation, key):
        if observation.ofvs:
            list_val = [x for x in observation.ofvs if x.name == key]
            if list_val:
                return list_val[0].value
        return None

    def get_observation_value_as_date(self, observation, key):
        value = self.get_observation_value(observation, key)
        if value:
            return datetime.fromisoformat(value)
        return None

    def add_attribute_if_not_none(self, entity, name, value):
        if value:
            entity[0]['attributes'][name] = value

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
