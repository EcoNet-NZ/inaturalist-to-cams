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

from behave import *
from datetime import datetime, date
from dateutils import today, yesterday, two_years_ago
from hamcrest import assert_that, equal_to, none

import pyinaturalist

from features.support import observation_factory


@given(u'iNaturalist observation {inat_id} has {anything}')
def step_impl(context, inat_id, anything):
    pass


@when(u'we read the observation {inat_id}')
def step_impl(context, inat_id):
    client = pyinaturalist.iNatClient()
    context.observation = client.observations(inat_id)


@then(u'the returned Observation has the location set to None')
def step_impl(context):
    assert_that(context.observation.location, none())


@then(u'the returned Observation has the location set to latitude = {latitude:f} and longitude = {longitude:f}')
def step_impl(context, latitude, longitude):
    assert_that(context.observation.location[0], equal_to(latitude)), 'latitude'
    assert_that(context.observation.location[1], equal_to(longitude)), 'longitude'

@given(u'iNaturalist has a new observation')
@given(u'iNaturalist has a new OMB observation')
def step_impl(context):
    context.observation = observation_factory.ObservationFactory()


@given(u'iNaturalist has a new OMB observation with id of {inat_id}')
def step_impl(context, inat_id):
    context.observation = observation_factory.ObservationFactory(id=inat_id)


@given(u'iNaturalist has a new OMB observation observed at {observation_date:ti}')
def step_impl(context, observation_date):
    context.observation = observation_factory.ObservationFactory(observed_on=observation_date)


@given(u'iNaturalist has a new OMB observation with id {inat_id} observed at {observation_date:ti}')
def step_impl(context, inat_id, observation_date):
    context.observation = observation_factory.ObservationFactory(id=inat_id, observed_on=observation_date)

@given(u"iNaturalist has an existing observation at 'latitude': {lat:f}, 'longitude': {lon:f}")
@given(u"iNaturalist has a new observation at 'latitude': {lat:f}, 'longitude': {lon:f}")
@given(u"iNaturalist has a new OMB observation at 'latitude': {lat:f}, 'longitude': {lon:f}")
@given(u"iNaturalist has an existing OMB observation at 'latitude': {lat:f}, 'longitude': {lon:f}")
def step_impl(context, lat, lon):
    context.observation = observation_factory.ObservationFactory(location=(lat, lon))

@given(u"the iNaturalist location is updated to 'latitude': {lat:f}, 'longitude': {lon:f}")
@given(u"the geolocation is updated to 'latitude': {lat:f}, 'longitude': {lon:f}")
def step_impl(context, lat, lon):
    context.observation.location = (lat, lon)


@given(u'iNaturalist has a new OMB observation with id {inat_id} without location')
def step_impl(context, inat_id):
    context.observation = observation_factory.ObservationFactory(id=inat_id, location=None)


@given(u'iNaturalist has a new observation for taxon {inaturalist_taxon} with ancestors [{ancestor_list}]')
def step_impl(context, inaturalist_taxon, ancestor_list):
    taxon = pyinaturalist.Taxon()
    taxon.id = inaturalist_taxon
    taxon.ancestor_ids = ancestor_list.split(',')
    context.observation = observation_factory.ObservationFactory(taxon=taxon)


@given(u'iNaturalist has a new observation with id {inat_id} for taxon {inaturalist_taxon} with ancestors [{ancestor_list}]')
def step_impl(context, inat_id, inaturalist_taxon, ancestor_list):
    taxon = pyinaturalist.Taxon()
    taxon.id = inaturalist_taxon
    taxon.ancestor_ids = ancestor_list.split(',')
    context.observation = observation_factory.ObservationFactory(id=inat_id, taxon=taxon)


# @given(u'iNaturalist has a new OMB observation for taxon {inaturalist_taxon}')
# def step_impl(context, inaturalist_taxon):
#     taxon = pyinaturalist.Taxon()
#     taxon.id = inaturalist_taxon
#     context.observation = observation_factory.ObservationFactory(taxon=taxon)
#
#
# @given(u'iNaturalist has a new OMB observation with id {inat_id} for taxon {inaturalist_taxon}')
# def step_impl(context, inat_id, inaturalist_taxon):
#     taxon = pyinaturalist.Taxon()
#     taxon.id = inaturalist_taxon
#     context.observation = observation_factory.ObservationFactory(id=inat_id, taxon=taxon)
#

@given(u"iNaturalist has a new OMB observation with description set to '{value}'")
def step_impl(context, value):
    context.observation = observation_factory.ObservationFactory(description=value)


@given(u"iNaturalist has a new OMB observation with '{field}' set to {value:g}")
@given(u"iNaturalist has a new OMB observation with '{field}' set to '{value}'")
@given(u"iNaturalist has a new OMB observation with date '{field}' set to '{value:ti}'")
def step_impl(context, field, value):
    ofvs = [pyinaturalist.ObservationFieldValue(name=field, value=value)]
    context.observation = observation_factory.ObservationFactory(ofvs=ofvs)


@given(u"iNaturalist has a new OMB observation with  '{field}' set to {value:g} and '{field2}' set to {value2:g}")
@given(u"iNaturalist has a new OMB observation with  '{field}' set to '{value}' and '{field2}' set to '{value2}'")
def step_impl(context, field, value, field2, value2):
    ofvs = [pyinaturalist.ObservationFieldValue(name=field, value=value),
            pyinaturalist.ObservationFieldValue(name=field2, value=value2)]
    context.observation = observation_factory.ObservationFactory(ofvs=ofvs)


@given(u"iNaturalist has a new OMB observation with quality_grade {grade}")
def step_impl(context, grade):
    context.observation = observation_factory.ObservationFactory(quality_grade=grade)


@given(u"iNaturalist has a new OMB observation observed at {observed_on} with no date controlled and no date of status update")
def step_impl(context, observed_on):
    context.observation = observation_factory.ObservationFactory(observed_on=observed_on)


@given(u'iNaturalist has a new OMB observation observed at {observed_on} with date controlled of {controlled_on:ti} and no date of status update')
def step_impl(context, observed_on, controlled_on):
    ofvs = [pyinaturalist.ObservationFieldValue(name='Date controlled', value=controlled_on)]
    context.observation = observation_factory.ObservationFactory(observed_on=observed_on, ofvs=ofvs)


@given(u'iNaturalist has a new OMB observation observed at {observed_on} with no date controlled and date of status update of {status_updated_on:ti}')
def step_impl(context, observed_on, status_updated_on):
    ofvs = [pyinaturalist.ObservationFieldValue(name='Date of status update', value=status_updated_on)]
    context.observation = observation_factory.ObservationFactory(observed_on=observed_on, ofvs=ofvs)


@given(
    u'iNaturalist has a new OMB observation observed at {observed_on} with date controlled of {controlled_on:ti} and date of status update of {status_updated_on:ti}')
def step_impl(context, observed_on, controlled_on, status_updated_on):
    ofvs = [pyinaturalist.ObservationFieldValue(name='Date controlled', value=controlled_on),
            pyinaturalist.ObservationFieldValue(name='Date of status update', value=status_updated_on)]
    context.observation = observation_factory.ObservationFactory(observed_on=observed_on, ofvs=ofvs)


@given(u'iNaturalist has a new OMB observation with DateVisitMade before the previous 1st July')
def step_impl(context):
    date_today = date.today()
    if date_today.month >= 7:
        year = date_today.year
    else:
        year = date_today.year - 1
    date_visit_made = str(year) + '-06-30T12:34:56+12:00'
    context.observation = observation_factory.ObservationFactory(observed_on=date_visit_made)


@given(u"iNaturalist has a new OMB observation with '{date_field}' before the previous 1st July")
def step_impl(context, date_field):
    date_today = date.today()
    if date_today.month >= 7:
        year = date_today.year
    else:
        year = date_today.year - 1
    date_value = datetime.fromisoformat(str(year) + '-06-30')
    ofvs = [pyinaturalist.ObservationFieldValue(name=date_field, value=date_value)]
    context.observation = observation_factory.ObservationFactory(ofvs=ofvs)


@given(u'iNaturalist has a new OMB observation with DateVisitMade set to the previous 1st July')
def step_impl(context):
    date_today = date.today()
    if date_today.month >= 7:
        year = date_today.year
    else:
        year = date_today.year - 1
    date_visit_made = str(year) + '-07-01T06:44:22+12:00'
    context.observation = observation_factory.ObservationFactory(observed_on=date_visit_made)


@given(u'iNaturalist has a new OMB observation with DateVisitMade set to today')
def step_impl(context):
    now = datetime.now().astimezone()
    context.observation = observation_factory.ObservationFactory(observed_on=now)


@given(u"iNaturalist has a new OMB observation with 'observed_on' = yesterday and '{date_field}' = today and '{name}' = '{value}'")
def step_impl(context, date_field, name, value):
    ofvs = [pyinaturalist.ObservationFieldValue(name=date_field, value=today().astimezone()),
            pyinaturalist.ObservationFieldValue(name=name, value=value)]
    context.observation = observation_factory.ObservationFactory(observed_on=yesterday().astimezone(), ofvs=ofvs)


@given(u"iNaturalist has a new OMB observation with 'observed_on' = yesterday")
def step_impl(context):
    ofvs = []
    context.observation = observation_factory.ObservationFactory(observed_on=yesterday().astimezone(), ofvs=ofvs)


@given(u"iNaturalist has a new OMB observation with 'observed_on' = 2 years ago")
def step_impl(context):
    ofvs = []
    context.observation = observation_factory.ObservationFactory(observed_on=two_years_ago().astimezone(), ofvs=ofvs)


@given(u"'{date_field}' = today")
@given(u"'{date_field}' is updated to today")
def step_impl(context, date_field):
    ofv = pyinaturalist.ObservationFieldValue(name=date_field, value=today().astimezone())
    context.observation.ofvs = context.observation.ofvs + [ofv]


@given(u"'{date_field}' = yesterday")
@given(u"'{date_field}' is updated to yesterday")
@given(u"the iNaturalist '{date_field}' is updated")
def step_impl(context, date_field):
    ofv = pyinaturalist.ObservationFieldValue(name=date_field, value=yesterday().astimezone())
    context.observation.ofvs = context.observation.ofvs + [ofv]


@given(u"'{field}' = '{value}'")
@given(u"the '{field}' are updated to '{value}'")
@given(u"'{field}' is updated to '{value}'")
@given(u"'{field}' is set to '{value}'")
def step_impl(context, field, value):
    ofv = pyinaturalist.ObservationFieldValue(name=field, value=value)
    if context.observation.ofvs is None:
        context.observation.ofvs = []
    context.observation.ofvs = context.observation.ofvs + [ofv]
    print(f'Updated observation is {context.observation} with ofvs {context.observation.ofvs}')


@given(u"iNaturalist has a new OMB observation with '{date_field}' = today and '{name}' = '{value}'")
def step_impl(context, date_field, name, value):
    ofvs = [pyinaturalist.ObservationFieldValue(name=date_field, value=today().astimezone()),
            pyinaturalist.ObservationFieldValue(name=name, value=value)]
    context.observation = observation_factory.ObservationFactory(ofvs=ofvs)


@given(u"iNaturalist has an existing OMB observation which has been synced")
def step_impl(context):
    context.observation = observation_factory.ObservationFactory()
    context.cams_feature, context.global_id = context.synchroniser.sync_observation(context.observation)


@given(u"that observation has been synced")
def step_impl(context):
    context.cams_feature, context.global_id = context.synchroniser.sync_observation(context.observation)


@given(u"the OMB observation is verified by another user")
def step_impl(context):
    verification = pyinaturalist.Identification(id=22334455, uuid='22334455', created_at=today().astimezone(), current_taxon=True, taxon=context.observation.taxon)
    context.observation.identifications = [verification]


@given(u"the quality grade is updated to '{grade}'")
def step_impl(context, grade):
    context.observation.quality_grade = grade
