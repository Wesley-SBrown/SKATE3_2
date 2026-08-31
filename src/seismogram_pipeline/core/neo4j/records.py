# src/seismogram_pipeline/core/neo4j/records.py

import json
from PIL import Image
from pathlib import Path
from typing import Union

from src.seismogram_pipeline.core.neo4j.connector import get_driver
from src.seismogram_pipeline.core.verify_network import verify_and_access_share
from src.seismogram_pipeline.core.neo4j.utils.parsers import (
    _group_records_by_station, _parse_datetime
)

def save_box_locally(
    box_filename: str,
    debug: bool = True,
    cache_dir: str = "./box_cache"
) -> None:
    raw_data_path = verify_and_access_share()
    if not raw_data_path:
        return

    folder_path = raw_data_path.joinpath(box_filename)

    if not folder_path.exists() or not folder_path.is_dir():
        raise ValueError(f"{folder_path.name} doesn't exist / isn't a folder")

    records = []
    
    for item in folder_path.iterdir():
        if item.suffix != ".tif":
            continue
        stem = item.stem

        contents = stem.split('_')

        record_type = None
        pier = None
        if '.' in contents[2]:
            record_type, pier = contents[2].split(".")

        file_size = item.stat().st_size
        width, height, color_mode, resolution = None, None, None, None

        try:
            with Image.open(item) as img:
                width, height = img.size
                color_mode = img.mode

                # since the resolution should be the same for x & y, just need extract one
                # should be the same across all the records, but good in case
                x_res_tag = img.tag.get(282) if hasattr(img, "tag") else None
                if x_res_tag:
                    val = x_res_tag[0]
                    if isinstance(val, tuple) and len(val) == 2:
                        resolution = float(val[0]) / float(val[1])
                    else:
                        resolution = float(val)

                icc_bytes = img.info.get('icc_profile')
            if icc_bytes:
                # Decode the raw bytes safely, ignoring unreadable binary characters
                icc_string = icc_bytes.decode('ascii', errors='ignore')
                
                if 'Adobe RGB (1998)' in icc_string:
                    color_profile = 'Adobe RGB (1998)'
                elif 'sRGB' in icc_string:
                    color_profile = 'sRGB'
                elif 'DeviceRGB' in icc_string:
                    color_profile = 'DeviceRGB'
                else:
                    color_profile = "Custom/Unknown ICC Profile"
        except Exception as e:
            if debug:
                print(f"[ERROR]: Failed to parse Tiff metadata for {stem}: {e}")

        record = {
            "recordName" : stem,
            "networkCode": contents[0],
            "stationCode": contents[1],
            "recordType": record_type if record_type else contents[2],
            "pier": pier if pier else None,
            "period": contents[3],
            "gain": contents[4],
            "orientation": contents[5],
            "dateTime": _parse_datetime(contents[6], contents[7]),
            "side": contents[8] if contents[8].isdigit() else "unknown",
            "fileSize": file_size,
            "width": width,
            "height": height,
            "colorMode": color_mode,
            "resolution": resolution,
            "colorProfile": color_profile
        }

        clean_record = {k: v for k, v in record.items() if v is not None}
        if debug:
            print(clean_record)
            break
        records.append(clean_record)

    print(len(records))

    if not debug:
        box_num = box_filename.split(" ")[1]
        station_data = _group_records_by_station(records=records)

        if station_data is None:
            raise ValueError(f"Failed to retrieve all station data")
        
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        cache_file = Path(cache_dir) / f"box_{box_num}_cache.json"

        cache_paylod = {
            "box_num": box_num,
            "station_data": json.dumps(station_data)
        }

        with open(cache_file, "w") as f:
            json.dump(cache_paylod, f, indent=4)

        print(f"[SUCCESS] Saved parsed record data from box: {box_num} to {cache_file}!")
        print(f"Disconnect from network VPN to upload to Neo4j")

def load_box_from_cache(
    box_num: Union[str, int],
    cache_dir: str = "./box_cache"
) -> None:
    """
    Uploaded cached record metadata to Neo4j instance 
    """
    cache_file = Path(cache_dir) / f"box_{box_num}_cache.json"
    if not cache_file.exists():
        raise FileNotFoundError(f"No local cache found for Box {box_num} at {cache_file}")

    with open(cache_file, "r") as f:
        cache_data = json.load(f)

    box_num = cache_data["box_num"]
    station_data = cache_data["station_data"]

    temp_station_dict = json.loads(station_data)
    station_codes = list(temp_station_dict.keys())

    if station_codes is None:
        raise ValueError(f"Sation codes missing for box: {box_num}")

    driver = get_driver()
    driver.verify_connectivity()
    try: 
        driver.execute_query("""
            CREATE CONSTRAINT station_id_unique
            IF NOT EXISTS FOR (s:Station)
            REQUIRE s.station_code IS UNIQUE
        """)

        driver.execute_query("""
            CREATE CONSTRAINT record_name_unique
            IF NOT EXISTS FOR (r:Record)
            REQUIRE r.recordName IS UNIQUE
        """)
        
        query = """
        MATCH (b:Box {boxNum: $box_num})
        SET b.stationData = $station_data

        // iterate through station codes and add relationships
        WITH b
        UNWIND $station_codes as code
        MATCH (s:Station {stationCode: code})
        MERGE (b)-[:CONTAINS_DATA_FOR]->(s)
        """

        driver.execute_query(
            query, box_num=box_num, 
            station_data=station_data,
            station_codes=station_codes 
        )
        print(f"Successfully updated Box {box_num} with appended station data and relationships.")
    except Exception as e:
        print(f"Failed to execute queries to Neo4J: {e}")
        print("Ensure disconnected from VPN")
    finally:
        driver.close()
    