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
Migration script to update existing CAMS records with RecordedBy and RecordedDate information.

This script fetches existing CAMS records that don't have RecordedBy information,
retrieves the corresponding iNaturalist observations, and determines the user_id based on:
1. The updater of the 'Date controlled' field (if it has a value)
2. The updater of the 'Date of status update' field (if it has a value)
3. The observation's user (fallback)

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
    """Migration class to update existing CAMS records with RecordedBy information"""
    
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
        """Process a single CAMS record"""
        object_id = record.get('OBJECTID')
        inat_ref = record.get('iNatRef')
        
        if not inat_ref:
            logging.warning(f"Record {object_id} has no iNatRef, skipping")
            self.skipped_count += 1
            return
        
        logging.debug(f"Processing record {object_id} with iNaturalist ID {inat_ref}")
        
        try:
            # Fetch fresh observation data from iNaturalist
            observation = inaturalist_reader.INatReader.get_observation_with_id(inat_ref)
            
            # Extract the recorded by information using the new approach
            # First flatten the observation to get the date fields
            inat_observation = inaturalist_reader.INatReader.flatten(observation)
            
            # Then use the translator to get the user_id
            from inat_to_cams.translator import INatToCamsTranslator
            translator_instance = INatToCamsTranslator()
            visit_date, visit_status, user_id, username = translator_instance.calculate_visit_date_and_status_and_user(inat_observation, observation)
            
            # Get recorded_date from observation
            if hasattr(observation, 'updated_at') and observation.updated_at:
                recorded_date = observation.updated_at
            elif hasattr(observation, 'created_at') and observation.created_at:
                recorded_date = observation.created_at
            else:
                recorded_date = None
            
            if user_id and username and recorded_date:
                # Update the CAMS record
                if self.dry_run:
                    logging.info(f"[DRY RUN] Would update record {object_id} with RecordedByUserId: {user_id}, RecordedByUserName: {username}, RecordedDate: {recorded_date}")
                else:
                    self.update_cams_record(object_id, user_id, username, recorded_date)
                    logging.info(f"Updated record {object_id} with RecordedByUserId: {user_id}, RecordedByUserName: {username}")
                
                self.updated_count += 1
            else:
                logging.info(f"Missing user_id ({user_id}), username ({username}), or recorded_date ({recorded_date}) for record {object_id}, skipping")
                self.skipped_count += 1
                
        except Exception as e:
            logging.error(f"Error processing iNaturalist observation {inat_ref}: {e}")
            raise
    
    def get_records_missing_recorded_by(self, limit: Optional[int] = None) -> List[dict]:
        """Query CAMS for records where RecordedBy is null or empty"""
        
        # Query the Visits table for records without RecordedByUserId or RecordedByUserName
        where_clause = "RecordedByUserId IS NULL OR RecordedByUserId = '' OR RecordedByUserName IS NULL OR RecordedByUserName = ''"
        
        if limit:
            # Add a limit to the query for testing
            where_clause += f" AND OBJECTID <= (SELECT MIN(OBJECTID) + {limit - 1} FROM Visits_Table WHERE {where_clause})"
        
        logging.info(f"Querying CAMS for records where: {where_clause}")
        
        try:
            # Query the visits table
            visits_layer = self.cams.item.tables[0]  # Assuming visits table is the first table
            query_result = visits_layer.query(where=where_clause, out_fields=['OBJECTID', 'iNatRef', 'RecordedByUserId', 'RecordedByUserName', 'RecordedDate'])
            
            records = []
            for feature in query_result.features:
                records.append(feature.attributes)
            
            logging.info(f"Found {len(records)} records missing RecordedByUserId or RecordedByUserName information")
            return records
            
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
        description="Update existing CAMS records with RecordedBy and RecordedDate information"
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
