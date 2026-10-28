#!/usr/bin/env python
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

"""
Set effort_to_control from the current iNaturalist "Effort to control" value.

Covers every WeedLocations row whose SiteSource is iNaturalist_v2, and every
visit linked to those rows. A blank effort is stored as 1, matching the sync.

Usage:
    python migration/update_effort_fields.py --dry-run
    python migration/update_effort_fields.py --limit 20
    python migration/update_effort_fields.py
"""

import argparse
import logging
import time
from collections import defaultdict

from inat_to_cams import cams_interface, config, inaturalist_reader, setup_logging
from inat_to_cams.effort import effort_value
from migration.effort_updates import inat_id_for_instance, stored_attributes, updates_for_instance


PAGE_SIZE = 2000
INAT_SOURCE = 'iNaturalist_v2'
LOCATION_EFFORT_FIELD = config.cams_schema_config.cams_field_name('WeedLocations', 'Effort to control')
VISIT_EFFORT_FIELD = config.cams_schema_config.cams_field_name('Visits_Table', 'Effort to control')


def with_effort(row, field_name):
    """Copy a stored effort column onto effort_to_control."""
    mapped = dict(row)
    mapped['effort_to_control'] = row.get(field_name)
    mapped.pop(field_name, None)
    return mapped


def guid_key(value):
    if value is None:
        return None
    return str(value).strip().strip('{}').lower()


def query_all(layer, where, fields):
    rows = []
    offset = 0
    while True:
        result = layer.query(
            where=where,
            out_fields=fields,
            return_geometry=False,
            result_offset=offset,
            result_record_count=PAGE_SIZE,
        )
        features = result.features or []
        rows.extend(feature.attributes for feature in features)
        if not features:
            break
        offset += len(features)
        exceeded = getattr(result, 'exceededTransferLimit', False)
        if len(features) < PAGE_SIZE and not exceeded:
            break
    return rows


class UpdateEffortFields:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.cams = cams_interface.connection
        self.locations_updated = 0
        self.visits_updated = 0
        self.unchanged = 0
        self.skipped = 0
        self.errors = 0
        setup_logging.SetupLogging()
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            force=True,
        )

    def run(self, batch_size=100, limit=None):
        logging.info(f"Dry run: {self.dry_run}")
        locations = [
            with_effort(row, LOCATION_EFFORT_FIELD)
            for row in query_all(
                self.cams.layer,
                f"SiteSource = '{INAT_SOURCE}'",
                ['OBJECTID', 'GlobalID', LOCATION_EFFORT_FIELD, 'iNatURL'],
            )
        ]
        logging.info(f"Found {len(locations)} iNaturalist weed instances")
        if limit is not None:
            locations = locations[:limit]
            logging.info(f"Limited to {len(locations)} weed instances")

        location_by_guid = {}
        for location in locations:
            key = guid_key(location.get('GlobalID'))
            if key:
                location_by_guid[key] = location

        visits = [
            with_effort(row, VISIT_EFFORT_FIELD)
            for row in query_all(
                self.cams.table,
                '1=1',
                ['OBJECTID', 'GUID_visits', 'iNatRef', VISIT_EFFORT_FIELD],
            )
        ]
        visits_by_guid = defaultdict(list)
        for visit in visits:
            key = guid_key(visit.get('GUID_visits'))
            if key in location_by_guid:
                visits_by_guid[key].append(visit)

        pending_locations = []
        pending_visits = []
        for location in locations:
            key = guid_key(location.get('GlobalID'))
            instance_visits = visits_by_guid.get(key, [])
            try:
                planned = self.plan(location, instance_visits)
            except Exception as error:
                logging.error(f"Weed instance {location.get('OBJECTID')} failed: {error}")
                self.errors += 1
                continue
            if planned is None:
                continue
            location_updates, visit_updates = planned
            if not location_updates and not visit_updates:
                self.unchanged += 1
                continue
            pending_locations.extend(location_updates)
            pending_visits.extend(visit_updates)
            if len(pending_locations) + len(pending_visits) >= batch_size:
                self.flush(pending_locations, pending_visits)
                pending_locations = []
                pending_visits = []
                time.sleep(1)
        self.flush(pending_locations, pending_visits)
        logging.info(
            f"Locations updated: {self.locations_updated}. "
            f"Visits updated: {self.visits_updated}. "
            f"Unchanged: {self.unchanged}. "
            f"Skipped: {self.skipped}. "
            f"Errors: {self.errors}."
        )

    def plan(self, location, visits):
        inat_id = inat_id_for_instance(location, visits)
        if not inat_id:
            logging.warning(f"Weed instance {location.get('OBJECTID')} has no iNaturalist id")
            self.skipped += 1
            return None
        observation = inaturalist_reader.INatReader.get_observation_with_id(inat_id)
        raw_effort = inaturalist_reader.INatReader.get_observation_value(observation, 'Effort to control')
        effort = effort_value(raw_effort)
        logging.info(f"Observation {inat_id} effort {effort} (field {raw_effort!r})")
        return updates_for_instance(location, visits, effort)

    def flush(self, location_updates, visit_updates):
        if not location_updates and not visit_updates:
            return
        if self.dry_run:
            logging.info(
                f"[DRY RUN] Would update {len(location_updates)} locations "
                f"and {len(visit_updates)} visits"
            )
            self.locations_updated += len(location_updates)
            self.visits_updated += len(visit_updates)
            return
        self.apply(self.cams.layer, location_updates, LOCATION_EFFORT_FIELD, 'locations')
        self.apply(self.cams.table, visit_updates, VISIT_EFFORT_FIELD, 'visits')
        self.locations_updated += len(location_updates)
        self.visits_updated += len(visit_updates)

    def apply(self, layer, updates, field_name, label):
        if not updates:
            return
        payload = [{'attributes': stored_attributes(row, field_name)} for row in updates]
        result = layer.edit_features(updates=payload)
        failures = [
            item for item in result.get('updateResults', [])
            if not item.get('success')
        ]
        if failures:
            raise RuntimeError(f"CAMS {label} update failed: {failures[0]}")
        logging.info(f"Updated {len(updates)} {label}")


def main():
    parser = argparse.ArgumentParser(description='Backfill effort to control from iNaturalist')
    parser.add_argument('--dry-run', action='store_true', help='Log the updates and write nothing')
    parser.add_argument('--batch-size', type=int, default=100)
    parser.add_argument('--limit', type=int, default=None, help='Maximum weed instances to process')
    args = parser.parse_args()
    UpdateEffortFields(dry_run=args.dry_run).run(batch_size=args.batch_size, limit=args.limit)


if __name__ == '__main__':
    main()
