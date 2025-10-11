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
Migration script to update existing CAMS records with RecordedByUserId, RecordedByUserName and RecordedDate information.

This script selectively updates specific visit records for each weed instance:

For each weed instance (iNaturalist observation):
1. If only one visit record exists:
   - Update it ONLY if WeedVisitStatus = 'RedGrowth'
   - Use original observer (ignore observation fields)

2. If multiple visit records exist:
   - Update first (oldest) record if WeedVisitStatus = 'RedGrowth' (use original observer)
   - Update most recent (last) record using field-based logic:
     * Date controlled field user (if field has value)
     * Date of status update field user (if field has value)  
     * Observation user (fallback)

The RecordedDate is set to the observation's updated_at or created_at timestamp.

Usage:
    python migration/update_recorded_by_fields.py [--dry-run] [--batch-size N] [--limit N]

Options:
    --dry-run       Show what would be updated without making changes
    --batch-size N  Process N records at a time (default: 50)
    --limit N       Limit to N total records (for testing)
"""

import argparse
import logging
import time
from datetime import datetime
from typing import List, Optional, Tuple

from inat_to_cams import cams_interface, inaturalist_reader, setup_logging


class UpdateRecordedByMigration:
    """Migration class to update existing CAMS records with RecordedByUserId and RecordedByUserName information"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.cams = cams_interface.connection
        self.updated_count = 0
        self.error_count = 0
        self.skipped_count = 0
        
        setup_logging.SetupLogging()
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s %(levelname)s %(message)s', 
            datefmt='%Y-%m-%d %H:%M:%S', 
            force=True
        )
    
    def migrate_existing_records(self, batch_size: int = 50, limit: Optional[int] = None):
        """Update existing CAMS records with RecordedBy information"""
        
        logging.info("Starting migration to update RecordedBy and RecordedDate fields")
        logging.info(f"Dry run mode: {self.dry_run}")
        logging.info(f"Batch size: {batch_size}")
        if limit:
            logging.info(f"Limiting to {limit} records")
        
        # Get all CAMS records that don't have RecordedBy populated
        records_to_update = self.get_records_missing_recorded_by(limit)
        
        if not records_to_update:
            logging.info("No records found that need updating")
            return
        
        logging.info(f"Found {len(records_to_update)} records to update")
        
        for i in range(0, len(records_to_update), batch_size):
            batch = records_to_update[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(records_to_update) + batch_size - 1) // batch_size
            
            logging.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} records)")
            
            for record in batch:
                try:
                    self.process_record(record)
                except Exception as e:
                    logging.error(f"Failed to process record {record.get('OBJECTID', 'unknown')}: {e}")
                    self.error_count += 1
            
            # Add delay between batches to respect API limits
            if i + batch_size < len(records_to_update):
                logging.info("Waiting 2 seconds before next batch...")
                time.sleep(2)
        
        # Print final statistics
        self.print_migration_summary()
    
    def process_record(self, record: dict):
        """Process a single CAMS record based on update rules"""
        object_id = record.get('OBJECTID')
        inat_ref = record.get('iNatRef')
        update_rule = record.get('_update_rule', 'unknown')
        
        if not inat_ref:
            logging.warning(f"Record {object_id} has no iNatRef, skipping")
            self.skipped_count += 1
            return
        
        logging.debug(f"Processing record {object_id} with iNaturalist ID {inat_ref} using rule '{update_rule}'")
        
        try:
            # Fetch fresh observation data from iNaturalist
            observation = inaturalist_reader.INatReader.get_observation_with_id(inat_ref)
            
            # Get recorded_date from observation (same for both rules)
            if hasattr(observation, 'updated_at') and observation.updated_at:
                recorded_date = observation.updated_at
            elif hasattr(observation, 'created_at') and observation.created_at:
                recorded_date = observation.created_at
            else:
                recorded_date = None
            
            # Apply different logic based on update rule
            if update_rule == 'first_red_growth':
                # Rule 1: Use original observer only (don't check observation fields)
                user_id = observation.user.id
                username = observation.user.login
                logging.debug(f"Using original observer for first RedGrowth record: {user_id} ({username})")
                
            elif update_rule == 'most_recent':
                # Rule 2: Use the implemented logic (check Date controlled/Status update fields)
                inat_observation = inaturalist_reader.INatReader.flatten(observation)
                
                from inat_to_cams.translator import INatToCamsTranslator
                translator_instance = INatToCamsTranslator()
                visit_date, visit_status, user_id, username = translator_instance.calculate_visit_date_and_status_and_user(inat_observation, observation)
                logging.debug(f"Using field-based logic for most recent record: {user_id} ({username})")
                
            else:
                logging.warning(f"Unknown update rule '{update_rule}' for record {object_id}, skipping")
                self.skipped_count += 1
                return
            
            if user_id and username and recorded_date:
                # Update the CAMS record
                if self.dry_run:
                    logging.info(f"[DRY RUN] Would update record {object_id} ({update_rule}) with RecordedByUserId: {user_id}, RecordedByUserName: {username}, RecordedDate: {recorded_date}")
                else:
                    self.update_cams_record(object_id, user_id, username, recorded_date)
                    logging.info(f"Updated record {object_id} ({update_rule}) with RecordedByUserId: {user_id}, RecordedByUserName: {username}")
                
                self.updated_count += 1
            else:
                logging.info(f"Missing user_id ({user_id}), username ({username}), or recorded_date ({recorded_date}) for record {object_id}, skipping")
                self.skipped_count += 1
                
        except Exception as e:
            logging.error(f"Error processing iNaturalist observation {inat_ref}: {e}")
            raise
    
    def get_records_missing_recorded_by(self, limit: Optional[int] = None) -> List[dict]:
        """Query CAMS for specific visit records that need updating per weed instance"""
        
        logging.info("Finding visit records that need RecordedByUserId/RecordedByUserName updates...")
        
        try:
            # Get all visits that are missing the new fields
            visits_layer = self.cams.item.tables[0]  # Assuming visits table is the first table
            where_clause = "RecordedByUserId IS NULL OR RecordedByUserId = '' OR RecordedByUserName IS NULL OR RecordedByUserName = ''"
            
            query_result = visits_layer.query(
                where=where_clause, 
                out_fields=['OBJECTID', 'iNatRef', 'RecordedByUserId', 'RecordedByUserName', 'RecordedDate', 'WeedVisitStatus'],
                order_by_fields='iNatRef, OBJECTID'  # Group by observation, then by creation order
            )
            
            all_records = []
            for feature in query_result.features:
                all_records.append(feature.attributes)
            
            logging.info(f"Found {len(all_records)} total records missing RecordedBy information")
            
            # Group records by iNatRef (observation ID)
            records_by_observation = {}
            for record in all_records:
                inat_ref = record.get('iNatRef')
                if inat_ref:
                    if inat_ref not in records_by_observation:
                        records_by_observation[inat_ref] = []
                    records_by_observation[inat_ref].append(record)
            
            # Select specific records to update for each observation
            records_to_update = []
            for inat_ref, observation_records in records_by_observation.items():
                # Sort by OBJECTID to get chronological order
                observation_records.sort(key=lambda x: x.get('OBJECTID', 0))
                
                if len(observation_records) == 1:
                    # Only one record: use rule 1 (first/oldest row if RedGrowth status)
                    record = observation_records[0]
                    if record.get('WeedVisitStatus') == 'RedGrowth':
                        record['_update_rule'] = 'first_red_growth'
                        records_to_update.append(record)
                        logging.debug(f"Selected single RedGrowth record for observation {inat_ref}: OBJECTID {record.get('OBJECTID')}")
                    else:
                        logging.debug(f"Skipping single non-RedGrowth record for observation {inat_ref}")
                else:
                    # Multiple records: use both rules
                    # Rule 1: First (oldest) row if it has RedGrowth status
                    first_record = observation_records[0]
                    if first_record.get('WeedVisitStatus') == 'RedGrowth':
                        first_record['_update_rule'] = 'first_red_growth'
                        records_to_update.append(first_record)
                        logging.debug(f"Selected first RedGrowth record for observation {inat_ref}: OBJECTID {first_record.get('OBJECTID')}")
                    
                    # Rule 2: Most recent (last) row
                    last_record = observation_records[-1]
                    last_record['_update_rule'] = 'most_recent'
                    records_to_update.append(last_record)
                    logging.debug(f"Selected most recent record for observation {inat_ref}: OBJECTID {last_record.get('OBJECTID')}")
            
            # Apply limit if specified
            if limit and len(records_to_update) > limit:
                records_to_update = records_to_update[:limit]
                logging.info(f"Limited to first {limit} records")
            
            logging.info(f"Selected {len(records_to_update)} specific records to update across {len(records_by_observation)} observations")
            return records_to_update
            
        except Exception as e:
            logging.error(f"Error querying CAMS for records: {e}")
            raise
    
    def update_cams_record(self, object_id: int, user_id: int, username: str, recorded_date: datetime):
        """Update a specific CAMS record with RecordedByUserId, RecordedByUserName and RecordedDate information"""
        
        try:
            # Prepare the update data
            update_data = [{
                'attributes': {
                    'OBJECTID': object_id,
                    'RecordedByUserId': str(user_id),
                    'RecordedByUserName': username,
                    'RecordedDate': int(recorded_date.timestamp() * 1000)  # Convert to milliseconds for ArcGIS
                }
            }]
            
            # Update the visits table
            visits_layer = self.cams.item.tables[0]  # Assuming visits table is the first table
            result = visits_layer.edit_features(updates=update_data)
            
            if result['updateResults'] and result['updateResults'][0]['success']:
                logging.debug(f"Successfully updated CAMS record {object_id}")
            else:
                error_msg = result['updateResults'][0].get('error', {}).get('description', 'Unknown error')
                raise Exception(f"CAMS update failed: {error_msg}")
                
        except Exception as e:
            logging.error(f"Error updating CAMS record {object_id}: {e}")
            raise
    
    def print_migration_summary(self):
        """Print summary of migration results"""
        logging.info("=" * 60)
        logging.info("MIGRATION SUMMARY")
        logging.info("=" * 60)
        logging.info(f"Records updated: {self.updated_count}")
        logging.info(f"Records skipped: {self.skipped_count}")
        logging.info(f"Records with errors: {self.error_count}")
        logging.info(f"Total processed: {self.updated_count + self.skipped_count + self.error_count}")
        
        # Note: RecordedBy now stores user_id directly, no username caching needed
        
        if self.dry_run:
            logging.info("This was a DRY RUN - no actual changes were made")
        
        logging.info("=" * 60)


def main():
    """Main entry point for the migration script"""
    
    parser = argparse.ArgumentParser(
        description="Update existing CAMS records with RecordedByUserId, RecordedByUserName and RecordedDate information"
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true', 
        help="Show what would be updated without making changes"
    )
    parser.add_argument(
        '--batch-size', 
        type=int, 
        default=50, 
        help="Process N records at a time (default: 50)"
    )
    parser.add_argument(
        '--limit', 
        type=int, 
        help="Limit to N total records (for testing)"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.batch_size <= 0:
        parser.error("batch-size must be greater than 0")
    
    if args.limit is not None and args.limit <= 0:
        parser.error("limit must be greater than 0")
    
    # Run the migration
    migration = UpdateRecordedByMigration(dry_run=args.dry_run)
    migration.migrate_existing_records(
        batch_size=args.batch_size,
        limit=args.limit
    )


if __name__ == "__main__":
    main()
