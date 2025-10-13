#!/usr/bin/env python3
"""
Test script to verify DynamoDB table schema and write a test record.
Run this to diagnose DynamoDB issues.
"""

import boto3
from decimal import Decimal
from datetime import datetime
import time

# Configuration
TABLE_NAME = "SmartHiveTelemetry"
REGION = "ap-southeast-2"
DEVICE_ID = "SmartHive_Pi"

def main():
    print("=" * 60)
    print("DynamoDB Diagnostic Test")
    print("=" * 60)
    
    # Initialize DynamoDB
    try:
        dynamodb = boto3.resource('dynamodb', region_name=REGION)
        table = dynamodb.Table(TABLE_NAME)
        print(f"✅ Connected to DynamoDB table: {TABLE_NAME}")
        print(f"   Region: {REGION}")
    except Exception as e:
        print(f"❌ Error connecting to DynamoDB: {e}")
        return
    
    # Check table description
    print("\n" + "-" * 60)
    print("Table Schema:")
    print("-" * 60)
    try:
        response = table.meta.client.describe_table(TableName=TABLE_NAME)
        table_info = response['Table']
        
        print(f"Table Name: {table_info['TableName']}")
        print(f"Table Status: {table_info['TableStatus']}")
        print(f"Item Count: {table_info.get('ItemCount', 0)}")
        
        print("\nKey Schema:")
        for key in table_info['KeySchema']:
            key_type = "Partition Key" if key['KeyType'] == 'HASH' else "Sort Key"
            print(f"  - {key['AttributeName']} ({key_type})")
        
        print("\nAttribute Definitions:")
        for attr in table_info['AttributeDefinitions']:
            print(f"  - {attr['AttributeName']}: {attr['AttributeType']}")
            
    except Exception as e:
        print(f"❌ Error describing table: {e}")
        return
    
    # Test write
    print("\n" + "-" * 60)
    print("Testing Write Operation:")
    print("-" * 60)
    
    test_item = {
        'SmartHive_Pi': DEVICE_ID,  # Partition key (matching your actual table schema)
        'timestamp': int(time.time()),
        'temperature': Decimal('34.5'),
        'humidity': Decimal('58.2'),
        'vibration_rms': Decimal('0.0521'),
        'sound_db': Decimal('52.3'),
        'sound_freq': Decimal('265.0')
    }
    
    print(f"Writing test item:")
    print(f"  SmartHive_Pi: {test_item['SmartHive_Pi']}")
    print(f"  timestamp: {test_item['timestamp']}")
    print(f"  temperature: {test_item['temperature']}")
    
    try:
        response = table.put_item(Item=test_item)
        print("✅ Write successful!")
        print(f"   Response: {response['ResponseMetadata']['HTTPStatusCode']}")
        
        readable_time = datetime.fromtimestamp(test_item['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        print(f"   Record timestamp: {readable_time}")
        
    except Exception as e:
        print(f"❌ Write failed: {e}")
        print("\nDEBUG: Item that failed to write:")
        for key, value in test_item.items():
            print(f"  {key}: {value} (type: {type(value).__name__})")
        return
    
    # Test query
    print("\n" + "-" * 60)
    print("Testing Query Operation:")
    print("-" * 60)
    
    try:
        response = table.query(
            KeyConditionExpression='SmartHive_Pi = :device_id',  # Match actual partition key name
            ExpressionAttributeValues={
                ':device_id': DEVICE_ID
            },
            ScanIndexForward=False,  # Sort descending (newest first)
            Limit=5
        )
        
        items = response['Items']
        print(f"✅ Query successful! Found {len(items)} recent records:")
        
        for idx, item in enumerate(items, 1):
            ts = datetime.fromtimestamp(item['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            temp = item.get('temperature', 'N/A')
            hum = item.get('humidity', 'N/A')
            print(f"   {idx}. {ts} | Temp: {temp}°C | Humidity: {hum}%")
            
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! DynamoDB is working correctly.")
    print("=" * 60)

if __name__ == "__main__":
    main()
