#!/usr/bin/env python3
"""
Update existing DynamoDB records to add timestamp_nz field.
This script adds human-readable NZ timestamps to all existing records.

Usage:
    python update_dynamodb_timestamps.py
"""

import boto3
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
    USE_ZONEINFO = True
except ImportError:
    import pytz
    USE_ZONEINFO = False
import config

def get_nz_time(timestamp):
    """Convert Unix timestamp to NZ time string."""
    if USE_ZONEINFO:
        nz_time = datetime.fromtimestamp(timestamp, tz=ZoneInfo('Pacific/Auckland'))
    else:
        # Use pytz for Windows compatibility
        nz_tz = pytz.timezone('Pacific/Auckland')
        utc_time = datetime.utcfromtimestamp(timestamp).replace(tzinfo=pytz.UTC)
        nz_time = utc_time.astimezone(nz_tz)
    return nz_time.strftime('%Y-%m-%d %H:%M:%S %Z')

def update_timestamps():
    """Add timestamp_nz field to all existing DynamoDB records."""
    
    print("Connecting to DynamoDB...")
    dynamodb = boto3.resource('dynamodb', region_name=config.AWS_REGION)
    table = dynamodb.Table(config.DYNAMODB_TABLE)
    
    print(f"Scanning table: {config.DYNAMODB_TABLE}")
    
    # Scan all items in the table
    response = table.scan()
    items = response['Items']
    
    # Handle pagination if there are more than 1MB of data
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])
    
    print(f"Found {len(items)} records to update")
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for item in items:
        try:
            # Skip if timestamp_nz already exists
            if 'timestamp_nz' in item:
                skipped_count += 1
                continue
            
            # Get the Unix timestamp
            timestamp = int(item['timestamp'])
            device_id = item['device_id']
            
            # Convert to NZ time
            timestamp_nz = get_nz_time(timestamp)
            
            # Update the item in DynamoDB
            table.update_item(
                Key={
                    'device_id': device_id,
                    'timestamp': timestamp
                },
                UpdateExpression='SET timestamp_nz = :tz',
                ExpressionAttributeValues={
                    ':tz': timestamp_nz
                }
            )
            
            updated_count += 1
            print(f"✅ Updated: {device_id} @ {timestamp} → {timestamp_nz}")
            
        except Exception as e:
            error_count += 1
            print(f"❌ Error updating record: {e}")
    
    print("\n" + "="*60)
    print(f"Update Complete!")
    print(f"  ✅ Updated: {updated_count} records")
    print(f"  ⏭️  Skipped: {skipped_count} records (already have timestamp_nz)")
    print(f"  ❌ Errors:  {error_count} records")
    print("="*60)

if __name__ == "__main__":
    print("="*60)
    print("DynamoDB Timestamp Update Script")
    print("Adding NZ timezone to existing records")
    print("="*60)
    
    confirm = input("\nThis will update all records in DynamoDB. Continue? (yes/no): ")
    
    if confirm.lower() in ['yes', 'y']:
        update_timestamps()
    else:
        print("Operation cancelled.")
