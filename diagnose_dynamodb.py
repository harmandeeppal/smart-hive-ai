#!/usr/bin/env python3
"""
DynamoDB Diagnostic Script for Smart Hive AI
This script checks why data is not flowing to DynamoDB from Raspberry Pi
"""

import boto3
import os
from datetime import datetime
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

def print_header(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def check_aws_credentials():
    """Check if AWS credentials are configured"""
    print_header("1. AWS Credentials Check")
    
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS Credentials Valid")
        print(f"   Account: {identity['Account']}")
        print(f"   User ARN: {identity['Arn']}")
        print(f"   User ID: {identity['UserId']}")
        return True
    except Exception as e:
        print(f"❌ AWS Credentials ERROR: {e}")
        print("\n💡 Fix:")
        print("   1. Run: aws configure")
        print("   2. Or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        return False

def check_dynamodb_table(region='ap-southeast-2', table_name='SmartHiveTelemetry'):
    """Check if DynamoDB table exists and is accessible"""
    print_header("2. DynamoDB Table Check")
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name=region)
        table = dynamodb.Table(table_name)
        
        # Get table description
        response = table.meta.client.describe_table(TableName=table_name)
        table_info = response['Table']
        
        print(f"✅ Table EXISTS: {table_name}")
        print(f"   Region: {region}")
        print(f"   Status: {table_info['TableStatus']}")
        print(f"   Item Count: {table_info['ItemCount']}")
        print(f"   Size: {table_info['TableSizeBytes'] / 1024:.2f} KB")
        print(f"   Partition Key: {table_info['KeySchema'][0]['AttributeName']} ({table_info['KeySchema'][0]['KeyType']})")
        print(f"   Sort Key: {table_info['KeySchema'][1]['AttributeName']} ({table_info['KeySchema'][1]['KeyType']})")
        
        return table
    except Exception as e:
        print(f"❌ DynamoDB Table ERROR: {e}")
        print("\n💡 Fix:")
        print(f"   1. Check table exists in region: {region}")
        print(f"   2. Check IAM permissions for dynamodb:DescribeTable")
        return None

def check_recent_data(table, device_id='SmartHive_Pi', hours=24):
    """Check for recent data in DynamoDB"""
    print_header("3. Recent Data Check")
    
    try:
        # Calculate timestamp for X hours ago
        current_time = int(datetime.now().timestamp())
        cutoff_time = current_time - (hours * 3600)
        
        print(f"📊 Querying last {hours} hours of data...")
        print(f"   Device ID: {device_id}")
        print(f"   Current Unix Time: {current_time}")
        print(f"   Cutoff Unix Time: {cutoff_time}")
        
        # Query recent data
        response = table.query(
            KeyConditionExpression='device_id = :device_id AND #ts >= :cutoff_time',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':device_id': device_id,
                ':cutoff_time': cutoff_time
            },
            ScanIndexForward=False,  # Most recent first
            Limit=10
        )
        
        items = response.get('Items', [])
        
        if not items:
            print(f"\n❌ NO DATA found in last {hours} hours!")
            print(f"\n💡 This confirms data is NOT reaching DynamoDB from Raspberry Pi")
            
            # Check if ANY data exists for this device
            print(f"\n🔍 Checking if ANY data exists for device_id: {device_id}...")
            all_data_response = table.query(
                KeyConditionExpression='device_id = :device_id',
                ExpressionAttributeValues={':device_id': device_id},
                ScanIndexForward=False,
                Limit=1
            )
            
            if all_data_response.get('Items'):
                last_item = all_data_response['Items'][0]
                last_timestamp = last_item['timestamp']
                last_time = datetime.fromtimestamp(last_timestamp, tz=pytz.timezone('Pacific/Auckland'))
                gap_hours = (current_time - last_timestamp) / 3600
                
                print(f"\n⚠️  FOUND old data:")
                print(f"   Last Record Timestamp: {last_timestamp}")
                print(f"   Last Record Time: {last_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                print(f"   Data Gap: {gap_hours:.1f} hours")
                print(f"   Has timestamp_nz: {'timestamp_nz' in last_item}")
                
                if gap_hours > 1:
                    print(f"\n❌ ISSUE CONFIRMED: Data stopped flowing {gap_hours:.1f} hours ago")
            else:
                print(f"\n❌ NO DATA AT ALL for device_id: {device_id}")
                print(f"   This might be a different issue (wrong device ID?)")
            
            return []
        
        print(f"\n✅ Found {len(items)} recent records")
        print(f"\n📋 Latest 5 records:")
        
        for i, item in enumerate(items[:5], 1):
            timestamp = item['timestamp']
            dt = datetime.fromtimestamp(timestamp, tz=pytz.timezone('Pacific/Auckland'))
            
            print(f"\n{i}. Timestamp: {timestamp}")
            print(f"   Time: {dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(f"   Has timestamp_nz: {'timestamp_nz' in item}")
            if 'timestamp_nz' in item:
                print(f"   timestamp_nz value: {item['timestamp_nz']}")
            
            # Show sensor data
            sensors = [k for k in item.keys() if k not in ['device_id', 'timestamp', 'timestamp_nz']]
            print(f"   Sensors: {', '.join(sensors)} ({len(sensors)} total)")
        
        return items
        
    except Exception as e:
        print(f"❌ Query ERROR: {e}")
        import traceback
        traceback.print_exc()
        return []

def test_write_to_dynamodb(table, device_id='SmartHive_Pi'):
    """Test if we can write to DynamoDB"""
    print_header("4. DynamoDB Write Test")
    
    try:
        from decimal import Decimal
        
        test_timestamp = int(datetime.now().timestamp())
        
        # Create test item
        item = {
            'device_id': device_id + '_TEST',
            'timestamp': test_timestamp,
            'temperature': Decimal('25.5'),
            'humidity': Decimal('60.0'),
            'test_write': True
        }
        
        print(f"📝 Attempting test write...")
        print(f"   Device ID: {item['device_id']}")
        print(f"   Timestamp: {item['timestamp']}")
        
        # Write test item
        table.put_item(Item=item)
        
        print(f"\n✅ TEST WRITE SUCCESSFUL!")
        print(f"   This means your AWS credentials and IAM permissions are correct")
        print(f"   The issue is likely in the container's code or configuration")
        
        # Clean up test item
        print(f"\n🧹 Cleaning up test record...")
        table.delete_item(
            Key={
                'device_id': item['device_id'],
                'timestamp': item['timestamp']
            }
        )
        print(f"✅ Test record deleted")
        
        return True
        
    except Exception as e:
        print(f"❌ TEST WRITE FAILED: {e}")
        print(f"\n💡 Fix:")
        print(f"   1. Check IAM permissions for dynamodb:PutItem")
        print(f"   2. Verify AWS credentials in container")
        import traceback
        traceback.print_exc()
        return False

def check_container_config():
    """Check configuration that should be used in container"""
    print_header("5. Container Configuration Check")
    
    print("📋 Checking config.py settings...")
    
    try:
        import config
        
        print(f"\n✅ Configuration loaded successfully")
        print(f"   IS_MOCK_ENVIRONMENT: {config.IS_MOCK_ENVIRONMENT}")
        print(f"   ENABLE_DYNAMODB: {config.ENABLE_DYNAMODB}")
        print(f"   DYNAMODB_TABLE: {config.DYNAMODB_TABLE}")
        print(f"   AWS_REGION: {config.AWS_REGION}")
        print(f"   THING_NAME: {config.THING_NAME}")
        print(f"   TELEMETRY_INTERVAL_SECONDS: {config.TELEMETRY_INTERVAL_SECONDS}")
        
        # Check for issues
        issues = []
        
        if config.IS_MOCK_ENVIRONMENT:
            issues.append("⚠️  IS_MOCK_ENVIRONMENT is True (should be False on Raspberry Pi)")
        
        if not config.ENABLE_DYNAMODB:
            issues.append("❌ ENABLE_DYNAMODB is False (should be True)")
        
        if config.DYNAMODB_TABLE != 'SmartHiveTelemetry':
            issues.append(f"⚠️  DYNAMODB_TABLE is '{config.DYNAMODB_TABLE}' (expected 'SmartHiveTelemetry')")
        
        if config.AWS_REGION != 'ap-southeast-2':
            issues.append(f"⚠️  AWS_REGION is '{config.AWS_REGION}' (expected 'ap-southeast-2')")
        
        if issues:
            print(f"\n❌ CONFIGURATION ISSUES FOUND:")
            for issue in issues:
                print(f"   {issue}")
        else:
            print(f"\n✅ All configuration settings look correct")
        
        return len(issues) == 0
        
    except Exception as e:
        print(f"❌ Configuration loading ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_recommendations():
    """Generate recommendations based on findings"""
    print_header("6. Recommendations")
    
    print("""
Based on the diagnostic results above, here are potential issues and fixes:

🔧 ISSUE: Data gap after deploying to Raspberry Pi
   CAUSE: Container may not have AWS credentials mounted correctly
   FIX:
   1. Check docker-compose.yml has this line:
      volumes:
        - ~/.aws:/root/.aws:ro
   
   2. Verify AWS credentials exist on Raspberry Pi:
      ssh pi@raspberrypi.local
      ls -la ~/.aws/
      # Should show: credentials, config
   
   3. If missing, configure AWS CLI on Raspberry Pi:
      aws configure
      # Enter your access key, secret key, and region

🔧 ISSUE: ENABLE_DYNAMODB is False
   FIX:
   1. Edit config.py on Raspberry Pi:
      nano ~/smart-hive-ai/config.py
   
   2. Find line: ENABLE_DYNAMODB = False
   
   3. Change to: ENABLE_DYNAMODB = True
   
   4. Restart container:
      docker compose restart edge-app

🔧 ISSUE: Code shows "DynamoDB: Wrote record" but nothing in database
   CAUSE: Silent exception in write_to_dynamodb() method
   FIX:
   1. Check container logs for errors:
      docker logs smart-hive-edge | grep "DynamoDB write error"
   
   2. If you see errors, check IAM permissions:
      - dynamodb:PutItem
      - dynamodb:GetItem
      - dynamodb:Query

🔧 ISSUE: Wrong AWS credentials in container
   FIX:
   1. Test credentials FROM INSIDE container:
      docker exec smart-hive-edge python3 -c "import boto3; print(boto3.client('sts').get_caller_identity())"
   
   2. If this fails, credentials are not mounted correctly

🔧 ISSUE: Container using old code
   FIX:
   1. Pull latest code and rebuild:
      cd ~/smart-hive-ai
      git pull origin main
      docker compose down
      docker compose build --no-cache edge-app
      docker compose up -d
    """)

def main():
    """Main diagnostic routine"""
    print("=" * 60)
    print("  SMART HIVE AI - DYNAMODB DIAGNOSTIC TOOL")
    print("=" * 60)
    print("\n🔍 Checking why data is not flowing to DynamoDB...\n")
    
    # Run all checks
    creds_ok = check_aws_credentials()
    
    if not creds_ok:
        print("\n❌ CRITICAL: AWS credentials not configured. Fix this first!")
        return
    
    table = check_dynamodb_table()
    
    if not table:
        print("\n❌ CRITICAL: Cannot access DynamoDB table. Fix this first!")
        return
    
    recent_data = check_recent_data(table)
    test_write_ok = test_write_to_dynamodb(table)
    config_ok = check_container_config()
    
    # Generate recommendations
    generate_recommendations()
    
    # Final summary
    print_header("DIAGNOSTIC SUMMARY")
    
    print(f"\n✅ AWS Credentials: {'VALID' if creds_ok else 'INVALID'}")
    print(f"✅ DynamoDB Table: {'ACCESSIBLE' if table else 'NOT ACCESSIBLE'}")
    print(f"{'✅' if recent_data else '❌'} Recent Data: {len(recent_data) if recent_data else 0} records found")
    print(f"{'✅' if test_write_ok else '❌'} Test Write: {'SUCCESS' if test_write_ok else 'FAILED'}")
    print(f"{'✅' if config_ok else '❌'} Configuration: {'CORRECT' if config_ok else 'HAS ISSUES'}")
    
    if not recent_data and test_write_ok:
        print(f"\n🎯 ROOT CAUSE IDENTIFIED:")
        print(f"   - AWS credentials and permissions: ✅ WORKING")
        print(f"   - DynamoDB table: ✅ ACCESSIBLE")
        print(f"   - Manual write test: ✅ SUCCESS")
        print(f"   - Container data flow: ❌ NOT WORKING")
        print(f"\n💡 CONCLUSION:")
        print(f"   The issue is in the CONTAINER CODE or CONFIGURATION,")
        print(f"   NOT with AWS credentials or permissions.")
        print(f"\n   Most likely causes:")
        print(f"   1. ENABLE_DYNAMODB = False in config.py")
        print(f"   2. AWS credentials not mounted in container")
        print(f"   3. write_to_dynamodb() method has a bug")
        print(f"   4. Container using old code")

if __name__ == "__main__":
    main()
