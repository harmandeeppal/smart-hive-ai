"""
Timezone Utilities for Smart Hive AI
Handles conversion of Unix timestamps to New Zealand time (Pacific/Auckland)
"""
from datetime import datetime
from zoneinfo import ZoneInfo

# New Zealand timezone
NZ_TIMEZONE = ZoneInfo('Pacific/Auckland')

def unix_to_nz_datetime(unix_timestamp):
    """
    Convert Unix timestamp to NZ datetime object.
    
    Args:
        unix_timestamp (int or float): Unix epoch timestamp
        
    Returns:
        datetime: Timezone-aware datetime object in Pacific/Auckland timezone
        
    Example:
        >>> dt = unix_to_nz_datetime(1760358215)
        >>> print(dt.strftime('%Y-%m-%d %H:%M:%S %Z'))
        2025-10-15 14:30:15 NZDT
    """
    return datetime.fromtimestamp(unix_timestamp, tz=NZ_TIMEZONE)

def unix_to_nz_string(unix_timestamp, format_str='%Y-%m-%d %H:%M:%S %Z'):
    """
    Convert Unix timestamp to formatted NZ time string.
    
    Args:
        unix_timestamp (int or float): Unix epoch timestamp
        format_str (str): strftime format string (default includes timezone)
        
    Returns:
        str: Formatted datetime string in NZ time
        
    Example:
        >>> nz_time = unix_to_nz_string(1760358215)
        >>> print(nz_time)
        2025-10-15 14:30:15 NZDT
    """
    dt = unix_to_nz_datetime(unix_timestamp)
    return dt.strftime(format_str)

def format_dynamodb_item_timestamps(item):
    """
    Convert all timestamp fields in a DynamoDB item to NZ time strings.
    Useful for API responses.
    
    Args:
        item (dict): DynamoDB item dictionary
        
    Returns:
        dict: Item with 'timestamp_nz' field added
        
    Example:
        >>> item = {'device_id': 'Pi_4B_001', 'timestamp': 1760358215, 'temperature': 34.5}
        >>> formatted = format_dynamodb_item_timestamps(item)
        >>> print(formatted['timestamp_nz'])
        2025-10-15 14:30:15 NZDT
    """
    if 'timestamp' in item:
        item['timestamp_nz'] = unix_to_nz_string(int(item['timestamp']))
    return item

def get_current_nz_time():
    """
    Get current time in New Zealand timezone.
    
    Returns:
        datetime: Current NZ time as timezone-aware datetime object
    """
    return datetime.now(NZ_TIMEZONE)

def get_current_nz_string(format_str='%Y-%m-%d %H:%M:%S %Z'):
    """
    Get current time in New Zealand as formatted string.
    
    Args:
        format_str (str): strftime format string
        
    Returns:
        str: Current NZ time as formatted string
    """
    return get_current_nz_time().strftime(format_str)

# For backward compatibility with Python 3.8 (which doesn't have zoneinfo)
# If you're using Python 3.8 or earlier, uncomment this and install pytz:
# pip install pytz

# import pytz
# NZ_TIMEZONE = pytz.timezone('Pacific/Auckland')
# 
# def unix_to_nz_datetime(unix_timestamp):
#     dt_utc = datetime.utcfromtimestamp(unix_timestamp).replace(tzinfo=pytz.UTC)
#     return dt_utc.astimezone(NZ_TIMEZONE)
