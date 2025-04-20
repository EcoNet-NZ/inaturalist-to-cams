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
from behave import *
from hamcrest import assert_that, equal_to, close_to
from datetime import datetime
from dateutils import today, yesterday, two_years_ago

from inat_to_cams import exceptions

FLOAT_DELTA = 1e-9

@given(u'the visits table does not have a record with iNaturalist id {inat_id}')
def step_impl(context, inat_id):
    context.connection.delete_feature_with_id(inat_id)


@when(u'we process the observation')
def step_impl(context):
    try:
        cams_feature, context.global_id = context.synchroniser.sync_observation(context.observation)
        if not context.global_id:
            context.global_id = context.connection.get_feature_global_id(context.observation.id)
        context.exc = None
    except exceptions.InvalidObservationError as e:
        context.exc = e
    except TypeError as err:
        logging.exception(err)


@then(u'a WeedLocations feature is created with species \'{cams_taxon}\'')
def step_impl(context, cams_taxon):
    feature_attributes = context.connection.get_location_details(context.global_id)
    assert_that(feature_attributes['SpeciesDropDown'], equal_to(cams_taxon))

@then(u'the CAMS geolocation is set to \'latitude\': {y:f}, \'longitude\': {x:f}')
@then(u'the CAMS geolocation remains set to \'latitude\': {y:f}, \'longitude\': {x:f}')
@then(u'the CAMS weedlocation is set to \'latitude\': {y:f}, \'longitude\': {x:f}')
@then(u'the CAMS weedlocation remains set to \'latitude\': {y:f}, \'longitude\': {x:f}')
def step_impl(context, x, y):
    location = context.connection.get_location_wgs84(context.global_id)
    assert_that(location['x'], close_to(x, FLOAT_DELTA), "x")
    assert_that(location['y'], close_to(y, FLOAT_DELTA), "y")

@then(u'a WeedLocations feature is created at geopoint \'x\': {x:f}, \'y\': {y:f} in coordinate system EPSG:{epsg:d}')
@then(u'a WeedLocations feature is set to geopoint \'x\': {x:f}, \'y\': {y:f} in coordinate system EPSG:{epsg:d}')
def step_impl(context, x, y, epsg):
    location = context.connection.get_location(context.global_id)
    assert_that(location['x'], close_to(x, FLOAT_DELTA), "x")
    
    assert_that(location['y'], close_to(y,  FLOAT_DELTA), "y")
    assert_that(location['spatialReference']['latestWkid'], equal_to(epsg), "epsg")


@then(u'the CAMS iNaturalist location is recorded as \'latitude\': {y:f}, \'longitude\': {x:f}')
def step_impl(context, x, y):
    feature_attributes = context.connection.get_location_details(context.global_id)
    assert_that(feature_attributes['iNatLongitude'], equal_to(x), "x")
    assert_that(feature_attributes['iNatLatitude'], equal_to(y), "y")
   

@then(u'the visits table has {expected_count:d} record with iNaturalist id {inat_id}')
def step_impl(context, expected_count, inat_id):
    count = context.connection.visits_row_count(inat_id)
    context.id = inat_id
    assert count == expected_count, f'Expected {expected_count} rows in ArcGIS Visits table but found {count}'


@then(u'the visits table has {expected_count:d} records for this observation')
def step_impl(context, expected_count):
    context.id = context.observation.id
    count = context.connection.visits_row_count(context.id)
    assert count == expected_count, f'Expected {expected_count} rows in ArcGIS Visits table but found {count}'


@then(u'the WeedLocations feature has an associated record with {child_count:d} child visits record')
def step_impl(context, child_count):
    context.id = context.observation.id
    row_count = context.connection.visits_row_count_with_same_locations_feature_as_visits_row(context.id)
    assert_that(row_count, equal_to(child_count)), f'Expected {child_count} Visits records for feature, but found {row_count}'


@then(u"the visits record has '{field}' set to None")
def step_impl(context, field):
    row = context.connection.visits_row(str(context.observation.id), 0)
    assert_that(row[field], equal_to(None))


@then(u"the {index_str} visits record has date '{field}' set to '{date:ti}'")
@then(u"the visits record has date '{field}' set to '{date:ti}'")
def step_impl(context, field, date, index_str='first'):
    index = to_numeric(index_str)
    row = context.connection.visits_row(str(context.observation.id), index)
    actual_date_ts = row[field]
    actual_date = None
    if actual_date_ts:
        actual_date = datetime.fromtimestamp(actual_date_ts // 1000)
    assert_that(actual_date, equal_to(date))


@then(u"the {index_str} visits record has date '{field}' set to {date_str}")
@then(u"the visits record has date '{field}' set to '{date_str}'")
def step_impl(context, field, date_str, index_str='first'):
    if date_str == 'today':
        expected_date = today()
    elif date_str == 'yesterday':
        expected_date = yesterday()
    elif date_str == '2 years ago':
        expected_date = two_years_ago()
    else:
        raise ValueError(f'date_str {date_str} not found')

    context.execute_steps(f'''
        then the {index_str} visits record has date '{field}' set to '{expected_date}'
    ''')


@then(u"the {index_str} visits record has '{field}' set to {value:g}")
@then(u"the {index_str} visits record has '{field}' set to '{value}'")
@then(u"the visits record has '{field}' set to {value:g}")
@then(u"the visits record has '{field}' set to '{value}'")
def step_impl(context, field, value, index_str='first'):
    index = to_numeric(index_str)
    row = context.connection.visits_row(str(context.observation.id), index)
    assert_that(row[field], equal_to(value))


def to_numeric(index_str):
    if index_str == 'first':
        return 0
    elif index_str == 'second':
        return 1
    elif index_str == 'third':
        return 2
    else:
        raise ValueError(f'Value {index_str} not supported')


@then(u"the feature has '{field}' set to date '{date:ti}'")
def step_impl(context, field, date):
    feature_attributes = context.connection.get_location_details(context.global_id)
    actual_date = datetime.fromtimestamp(feature_attributes[field] // 1000)
    assert_that(actual_date, equal_to(date))


@then(u"the feature has '{field}' set to '{value}'")
@then(u"the feature has '{field}' set to {value:d}")
def step_impl(context, field, value):
    feature_attributes = context.connection.get_location_details(context.global_id)
    assert_that(feature_attributes[field], equal_to(value))


@then(u'the error "{message}" is logged')
def step_impl(context, message):
    # print(f'Log capture {context.log_capture.buffer}')
    assert (context.log_capture.find_event(message))


@then(u'the existing OMB observation is unchanged')
def step_impl(context):
    current_observation = context.reader.read_observation(context.observation.id)
    assert_that(current_observation, equal_to(context.cams_feature))
    # assert(context.log_capture.find_event(message))


@given(u'we read the updated observation')
def step_impl(context):
    context.updated_observation = context.reader.read_observation(context.observation.id)

@given(u'the CAMS geolocation has been manually updated to \'latitude\': {lat:f}, \'longitude\': {lon:f}')
def step_impl(context, lat, lon):
   observation = context.observation
   writer = context.writer
   writer.update_feature_geolocation(observation.id, lon, lat)

@given(u"the CAMS geoprivacy has been updated in CAMS to '{new_value}'")
def step_impl(context, new_value):
   observation = context.observation
   writer = context.writer
   writer.update_feature_geoprivacy(observation.id, new_value)

@given(u"the CAMS land ownership has been updated in CAMS to '{new_value}'")
def step_impl(context, new_value):
   observation = context.observation
   writer = context.writer
   writer.update_feature_land_ownership(observation.id, new_value)

@then(u'the updated observation is unchanged')
def step_impl(context):
    current_observation = context.reader.read_observation(context.observation.id)
    assert_that(current_observation, equal_to(context.updated_observation))

@given(u"a new visits record was created in CAMS with status '{status}' yesterday")
def step_impl(context, status):
    # Get the existing weed location feature from CAMS
    feature_attributes = context.connection.get_location_details(context.global_id)
    
    # Prepare a new visits record with yesterday's date
    new_visits_record = [{
        'attributes': {
            'GUID_visits': context.global_id,
            'DateCheck': yesterday().timestamp() * 1000,  # Convert to milliseconds timestamp
            'iNatRef': str(context.observation.id),
            'WeedVisitStatus': status
        }
    }]
    
    # Add the new visits record to CAMS
    results = context.connection.table.edit_features(adds=new_visits_record)
    assert len(results['addResults']) == 1
    assert results['addResults'][0]['success'], f"Error writing WeedVisits {results['addResults'][0]}"
    
    # Update the parent feature status to match the new visit
    update_feature = [{
        'attributes': {
            'GlobalID': context.global_id,
            'OBJECTID': feature_attributes['OBJECTID'],
            'ParentStatusWithDomain': 'YellowKilledThisYear'
        }
    }]
    
    context.connection.update_weed_location_layer_row(update_feature)

@given(u"the weed instance status was rolled over to '{status}' yesterday")
def step_impl(context, status):
    # Get the existing weed location feature from CAMS
    feature_attributes = context.connection.get_location_details(context.global_id)
    
    # Format yesterday's date as YYYY-MM-DD
    yesterday_formatted = yesterday().strftime('%Y-%m-%d')
    
    # Create audit log entry
    audit_log = f"{yesterday_formatted} Updated from RedGrowth to Purple based on Next Visit Date"
    
    # Update the feature with the new status and audit log
    update_feature = [{
        'attributes': {
            'GlobalID': context.global_id,
            'OBJECTID': feature_attributes['OBJECTID'],
            'ParentStatusWithDomain': status,
            'audit_log': audit_log
        }
    }]
    
    context.connection.update_weed_location_layer_row(update_feature)
