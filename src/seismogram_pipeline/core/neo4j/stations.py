# src/seismogram_pipeline/core/neo4j/stations.py

import pandas as pd
from pathlib import Path
from typing import Optional

from src.seismogram_pipeline.core.neo4j.connector import get_driver

def load_stations(
    station_filename: Optional[str] = None,
    station_path: Optional[str] = None,
    debug: bool = True
) -> None:
    if not station_path:
        if not station_filename:
            raise ValueError("Input filename or path missing")
        
        station_path = (Path(__file__)
                    .resolve()
                    .parents[2]
                    .joinpath("data/inputs")
                    ).joinpath(station_filename)
    cols = [
        'network_code', 'station_code', 'channel_code', 'location_code',
        'station_name', 'latitude', 'longitude', 'elevation',
        'on_date', 'off_date', 'instrument_depth'
    ]
    stations = pd.read_csv(station_path, names=cols, header=0)
    stations['instrument_depth'] = pd.to_numeric(
        stations['instrument_depth'].astype(str).str.rstrip("\\"), 
        errors="coerce"
    ).fillna(0).astype(int)
    
    stations['latitude'] = pd.to_numeric(stations['latitude'], errors="coerce")
    stations['longitude'] = pd.to_numeric(stations['longitude'], errors="coerce")
    stations['elevation'] = pd.to_numeric(stations['elevation'], errors="coerce")

    if debug:
        print(stations.info())
        print(stations.head(3))

    if not debug:
        driver = get_driver()
        driver.verify_connectivity()

        # create constraints for network and station
        driver.execute_query("""
            CREATE CONSTRAINT network_code_unique
            IF NOT EXISTS FOR (n:Network)
            REQUIRE n.networkCode IS UNIQUE
        """)

        driver.execute_query("""
            CREATE CONSTRAINT station_id_unique
            IF NOT EXISTS FOR (s:Station)
            REQUIRE s.stationCode IS UNIQUE
        """)

    station_data = []
    for _, row in stations.iterrows():
        station_dict = {
            "networkCode": row['network_code'],
            "stationCode": row['station_code'],
            "channelCode": row['channel_code'],
            "locationCode": row['location_code'] if row['location_code'] != "--" else None,
            "stationName": row["station_name"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "elevation": row["elevation"],
            "onDate": row['on_date'],
            "offDate": row['off_date'],
            "instrumentDepth": row['instrument_depth']
        }

        station_data.append({k: v for k, v in station_dict.items() if v is not None})

    if debug:
        print(station_data[0])

    if not debug:

        query = """
        UNWIND $stations as row

        // merge network node
        MERGE (n:Network {networkCode: row.networkCode})

        // merge station node
        MERGE (s:Station {stationCode: row.stationCode})
        ON CREATE SET
            s.stationName = row.stationName,
            s.latitude = row.latitude,
            s.longitude = row.longitude,
            s.elevation = row.elevation
        
        // connect network to station
        MERGE (n)-[:HAS_STATION]->(s)

        // create channel node
        CREATE (c:Channel {
            id: randomUUID(),
            channelCode: row.channelCode,
            locationCode: row.locationCode,
            on_date: row.onDate,
            off_date: row.offDate,
            instrumentDepth: row.instrumentDepth
        })

        // link station to channel
        MERGE (s)-[:HAS_CHANNEL]-(c)
        """

        driver.execute_query(query, stations=station_data)
        driver.close()

        print(f"Successfully loaded stations, networks, and channels with relationships")
