#!/usr/bin/env python3
"""
Check DynamoDB records for timestamp_nz field.
Useful for verifying if the fix is working.

Usage:
    python check_dynamodb_timestamps.py
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

def check_timestamps():
    """Check recent DynamoDB records for timestamp_nz field."""
    
    print("Connecting to DynamoDB...")
    dynamodb = boto3.resource('dynamodb', region_name=config.AWS_REGION)
    table = dynamodb.Table(config.DYNAMODB_TABLE)
    
    print(f"Querying table: {config.DYNAMODB_TABLE}")
    print(f"Device ID: {config.THING_NAME}")
    
    # Query the last 10 records
    response = table.query(
        KeyConditionExpression='device_id = :device',
        ExpressionAttributeValues={
            ':device': config.THING_NAME
        },
        ScanIndexForward=False,  # Most recent first
        Limit=10
    )
    
    items = response['Items']
    
    print(f"\n{'='*80}")
    print(f"Last 10 records:")
    print(f"{'='*80}\n")
    
    has_nz_count = 0
    missing_nz_count = 0
    
    for i, item in enumerate(items, 1):
        timestamp = int(item['timestamp'])
        dt = datetime.fromtimestamp(timestamp)
        
        has_nz = 'timestamp_nz' in item
        
        if has_nz:
            has_nz_count += 1
            status = "✅ HAS"
            nz_value = item['timestamp_nz']
        else:
            missing_nz_count += 1
            status = "❌ MISSING"
            nz_value = "(not present)"
        
        print(f"{i}. Unix: {timestamp}")
        print(f"   UTC:  {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"   NZ:   {status} timestamp_nz → {nz_value}")
        
        # Show sensor data
        sensors = []
        if 'temperature' in item:
            sensors.append(f"Temp: {item['temperature']}°C")
        if 'humidity' in item:
            sensors.append(f"Hum: {item['humidity']}%")
        if 'vibration_rms' in item:
            sensors.append(f"Vib: {item['vibration_rms']}")
        if 'sound_db' in item:
            sensors.append(f"Sound: {item['sound_db']}dB")
        
        print(f"   Data: {', '.join(sensors)}")
        print()
    
    print(f"{'='*80}")
    print(f"Summary:")
    print(f"  ✅ Records WITH timestamp_nz:    {has_nz_count}")
    print(f"  ❌ Records WITHOUT timestamp_nz: {missing_nz_count}")
    print(f"{'='*80}")
    
    if missing_nz_count > 0:
        print("\n💡 Tip: If all records are missing timestamp_nz:")
        print("   1. Check if the fix is deployed: docker logs smart-hive-edge")
        print("   2. Wait 60 seconds for next telemetry write")
        print("   3. Run this script again to verify new records")
        print("   4. Use update_dynamodb_timestamps.py to update old records")

if __name__ == "__main__":
    check_timestamps()
