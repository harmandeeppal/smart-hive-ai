# Timezone Configuration - New Zealand Time

## Overview
All timestamps in the Smart Hive AI system are stored as **Unix epoch timestamps** (seconds since Jan 1, 1970 UTC) in DynamoDB, but are **displayed in New Zealand time (Pacific/Auckland)** throughout the system.

## What Changed

### 1. **Dashboard Display (Frontend - JavaScript)**
- **File:** `dashboard/static/app.js`
- **Changes:**
  - `updateTimestamp()` function now displays full date/time in NZ timezone with explicit timezone indicator (NZDT/NZST)
  - `updateAiStatus()` function converts AI vision snapshot times to NZ time
  - Format: `15 Oct 2025, 14:30:15 NZDT/NZST`

**Before:**
```javascript
elements.lastUpdated.textContent = `Last Updated: ${new Date(timestamp * 1000).toLocaleTimeString()}`;
```

**After:**
```javascript
const nzTime = new Date(timestamp * 1000).toLocaleString('en-NZ', {
    timeZone: 'Pacific/Auckland',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
});
elements.lastUpdated.textContent = `Last Updated: ${nzTime} NZDT/NZST`;
```

### 2. **Backend Logging (Python)**
- **File:** `app.py`
- **Changes:** Console logs now show timestamps in NZ time with timezone indicator
- Format: `2025-10-15 14:30:15 NZDT`

**Before:**
```python
readable_time = datetime.fromtimestamp(item['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
```

**After:**
```python
from datetime import datetime
from zoneinfo import ZoneInfo
nz_time = datetime.fromtimestamp(item['timestamp'], tz=ZoneInfo('Pacific/Auckland'))
readable_time = nz_time.strftime('%Y-%m-%d %H:%M:%S %Z')
```

### 3. **Utility Module (New)**
- **File:** `timezone_utils.py`
- **Purpose:** Reusable functions for timezone conversion across the project
- **Key Functions:**
  - `unix_to_nz_datetime(timestamp)` - Convert Unix timestamp to NZ datetime object
  - `unix_to_nz_string(timestamp)` - Convert Unix timestamp to formatted NZ string
  - `format_dynamodb_item_timestamps(item)` - Add NZ time field to DynamoDB items for API responses
  - `get_current_nz_time()` - Get current NZ time

## Timezone Handling

### Storage (DynamoDB)
- **Format:** Unix timestamp (integer)
- **Example:** `1760358215`
- **Timezone:** UTC (inherent to Unix timestamps)
- **Advantage:** Timezone-agnostic, easy to convert to any timezone

### Display (Dashboard & Logs)
- **Timezone:** Pacific/Auckland (New Zealand)
- **Handles automatically:**
  - **NZDT** (New Zealand Daylight Time): UTC+13 (late Sep to early Apr)
  - **NZST** (New Zealand Standard Time): UTC+12 (early Apr to late Sep)
- **Format:** Human-readable with explicit timezone indicator

## Usage Examples

### Python (Backend)
```python
from timezone_utils import unix_to_nz_string, unix_to_nz_datetime

# Convert timestamp to NZ string
timestamp = 1760358215
nz_time = unix_to_nz_string(timestamp)
print(nz_time)  # Output: 2025-10-15 14:30:15 NZDT

# Get NZ datetime object
nz_dt = unix_to_nz_datetime(timestamp)
print(nz_dt.hour)  # 14 (2:30 PM NZ time)

# Format DynamoDB item for API response
item = {'device_id': 'Pi_4B_001', 'timestamp': 1760358215, 'temperature': 34.5}
formatted = format_dynamodb_item_timestamps(item)
print(formatted['timestamp_nz'])  # 2025-10-15 14:30:15 NZDT
```

### JavaScript (Frontend)
```javascript
// Convert Unix timestamp to NZ time
const timestamp = 1760358215;
const nzTime = new Date(timestamp * 1000).toLocaleString('en-NZ', {
    timeZone: 'Pacific/Auckland',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
});
console.log(nzTime);  // Output: 15 Oct 2025, 14:30:15
```

## Testing

### Verify Timezone Conversion
Run this Python snippet to test:
```python
from timezone_utils import unix_to_nz_string
import time

# Current time
current = int(time.time())
print(f"Current Unix timestamp: {current}")
print(f"Current NZ time: {unix_to_nz_string(current)}")

# Example timestamp
example = 1760358215
print(f"\nExample timestamp: {example}")
print(f"Example NZ time: {unix_to_nz_string(example)}")
```

### Check Dashboard
1. Open dashboard: `http://<raspberry-pi-ip>:5000`
2. Check "Last Updated" timestamp - should show NZ time with NZDT/NZST
3. When queen is detected, "Last Snapshot" should also show NZ time

### Check Logs
```bash
docker-compose logs -f edge-app | grep "DynamoDB"
```
Look for lines like:
```
✅ DynamoDB: Wrote record at 2025-10-15 14:30:15 NZDT (5 sensors)
```

## Python Requirements

### Python 3.9+ (Recommended)
Uses built-in `zoneinfo` module - **no extra dependencies needed** ✅

### Python 3.8 or Earlier
If using Python 3.8, install `pytz`:
```bash
pip install pytz
```
Then uncomment the pytz section at the bottom of `timezone_utils.py`.

## Browser Compatibility
The JavaScript `toLocaleString()` with `timeZone: 'Pacific/Auckland'` works in:
- ✅ Chrome 24+
- ✅ Firefox 52+
- ✅ Safari 10+
- ✅ Edge 14+
- ✅ All modern mobile browsers

## Future Enhancements

If you add historical data queries or API endpoints:

```python
# Example: API endpoint to query recent telemetry
from timezone_utils import format_dynamodb_item_timestamps
from flask import jsonify

@app.route('/api/telemetry/recent')
def get_recent_telemetry():
    # Query DynamoDB
    response = table.query(
        KeyConditionExpression='device_id = :device',
        ExpressionAttributeValues={':device': 'Pi_4B_001'},
        Limit=10,
        ScanIndexForward=False  # Most recent first
    )
    
    # Convert timestamps to NZ time
    items = [format_dynamodb_item_timestamps(item) for item in response['Items']]
    
    return jsonify(items)
```

This will add a `timestamp_nz` field to each item:
```json
{
  "device_id": "Pi_4B_001",
  "timestamp": 1760358215,
  "timestamp_nz": "2025-10-15 14:30:15 NZDT",
  "temperature": 34.5,
  "humidity": 58.2
}
```

## Summary
✅ **DynamoDB:** Stores Unix timestamps (timezone-agnostic)  
✅ **Dashboard:** Displays in NZ time (Pacific/Auckland)  
✅ **Console Logs:** Shows NZ time with timezone indicator  
✅ **Utility Functions:** Ready for future API development  
✅ **Automatic DST:** Handles NZDT ↔ NZST transitions automatically
