# src/seismogram_pipeline/core/neo4j/utils/parsers.py

from datetime import datetime
from typing import Any, Optional
from collections import defaultdict


def _group_records_by_station(
    records: list[dict[str,Any]]
) -> dict[defaultdict[list]]:
    station_data = defaultdict(list)
    for record in records:
        station_code = record.get("stationCode")
        if station_code:
            station_data[station_code].append(record)
    return station_data

def _parse_date(date_str: str) -> Optional[str]:
    """
    Converts YYYYMMDD to YYYY-MM-DD
    """
    if not date_str:
        return None
    date_str = date_str.strip()
    
    # sometimes date is only saved as YYYYMM
    if len(date_str) == 8:
        fmt = "%Y%m%d"
    elif len(date_str) == 6:
        fmt = "%Y%m"
    else:
        return None
        
    try:
        dt = datetime.strptime(date_str, fmt)
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None

def _parse_time(time_str: str) -> Optional[str]:
    """
    Converts 4-digit 24hr times to ISO format 'HH:MM:SS'
    Returns None if placeholder ('XXXX') or invalid format
    """
    if not time_str or time_str.upper() == 'XXXX' or len(time_str) != 4:
        return None
    try: 
        hour = time_str[:2]
        minute = time_str[2:]

        if not (hour.isdigit() and minute.isdigit()):
            return None
        
        return f"{hour}:{minute}:00"
    except Exception:
        return None

def _parse_datetime(date_str: str, time_str: str) -> Optional[str]:
    parsed_date = _parse_date(date_str)
    if not parsed_date:
        return None
        
    parsed_time = _parse_time(time_str)
    if parsed_time:
        # Returns an ISO compliant string (i.e. "1930-11-09T14:30:00")
        return f"{parsed_date}T{parsed_time}"
    
    # Fallback if time is 'XXXX' or invalid, keeping it strictly date-level
    return parsed_date