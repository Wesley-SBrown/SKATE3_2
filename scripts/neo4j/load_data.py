# scripts/neo4j/load_data.py

import uuid
import pandas as pd
from pathlib import Path
from typing import Optional
from src.seismogram_pipeline.core.neo4j.connector import get_driver


def load_indiv_excel_sheet(
    sheet_name: str,
    excel_filename: Optional[str] = None,
    input_path: Optional[str] = None, 
    debug: bool = True
) -> None:
    if not input_path:
        if not excel_filename:
            raise ValueError("Input filename or path missing")
        
        input_path = (Path(__file__)
                    .resolve()
                    .parents[2]
                    .joinpath("data/inputs")
                    ).joinpath(excel_filename)
    
    # define cols for sheet (may change per sheet)
    cols = ['verified_by', 'box_num', 'stack_num', 'from_year',
            'from_month', 'from_day', 'through_year', 'through_month', "through_day",
            'exceptions', 'notes', 'prev_no', 'comments', 'image_name', 'checked_out', 
            'name', 'scanned_date', 'scanned_by'
            ]

    # define range of cols to select
    cols_to_save = list(range(len(cols)))

    # select single sheet from excel file
    container = pd.read_excel(
                    input_path, sheet_name=sheet_name, 
                    skiprows=2, header=None, names=cols, 
                    usecols=cols_to_save
                )
    if debug:
        print(container.iloc[327, 5:])
    
    num_missing = int(container.tail(1)["box_num"].values[0])
    container = container[:-2]
    container["box_num"] = pd.to_numeric(container["box_num"], errors="coerce")
    container = container.dropna(subset=["box_num"])

    def safe_int(val):
        if pd.isna(val):
            return None
        try:
            return int(float(val)) 
        except (ValueError, TypeError):
            return None

    def build_date(row, prefix):
        y = safe_int(row.get(f'{prefix}_year'))
        m = safe_int(row.get(f'{prefix}_month'))
        d = safe_int(row.get(f'{prefix}_day'))

        if y is None:
            return None
        
        month_val = m if (m is not None and 1 <= m <= 12) else 1
        day_val = d if (d is not None and 1 <= d <= 31) else 1
        
        try:
            return f"{y:04d}-{month_val:02d}-{day_val:02d}"
        except ValueError:
            return str(y)

    # build from & through dates
    container["from_date"] = container.apply(lambda r: build_date(r, "from"), axis=1)
    container["through_date"] = container.apply(lambda r: build_date(r, "through"), axis=1)

    if debug:
        print(container.info())
        print(container.tail(10))

    if not debug:

        driver = get_driver()

        # ensure connected
        print("Testing connection...")
        driver.verify_connectivity()
        print("Connected successfully!")

        # create constraints
        driver.execute_query("""
            CREATE CONSTRAINT container_id_unique
            IF NOT EXISTS FOR (c:Container)
            REQUIRE c.id IS UNIQUE
        """)

        driver.execute_query("""
            CREATE CONSTRAINT box_id_unique
            IF NOT EXISTS FOR (b:Box)
            REQUIRE b.id IS UNIQUE
        """)

    # Create container node
    container_id = str(uuid.uuid4())
    container_name = sheet_name.split(" - ")[1]
    box_range_label = sheet_name.split(" - ")[0]

    if debug:
        print(f"Container ID: {container_id}")
        print(f"Container_name: {container_name}")
        print(f"Box range: {box_range_label}")
        print(f"Num missing: {num_missing}")


    box_data = []
    for _, row in container.iterrows():
        box_dict = {
            "id": str(uuid.uuid4()),
            "box_num": int(row["box_num"]),
            "stack_num": int(row["stack_num"]) if pd.notna(row["stack_num"]) else None,
            "from_date": row["from_date"],
            "through_date": row["through_date"],
            "exceptions": row["exceptions"] if pd.notna(row["exceptions"]) else None,
            "notes": row["notes"] if pd.notna(row["notes"]) else None,
            "prev_no": row["prev_no"] if pd.notna(row["prev_no"]) else None,
            "comments":row["comments"] if pd.notna(row["comments"]) else None,
            "image_name": row["image_name"] if pd.notna(row["image_name"]) else None,
            "checked_out": row["checked_out"] if pd.notna(row["checked_out"]) else None,
            "name": row["name"] if pd.notna(row["name"]) else None,
            "scanned_date": row["scanned_date"] if pd.notna(row["scanned_date"]) else None,
            "scanned_by": row["scanned_by"] if pd.notna(row["scanned_by"]) else None
        }
        clean_box_dict = {k: v for k, v in box_dict.items() if v is not None}
        box_data.append(clean_box_dict)

    if not debug:
        query = """
        MERGE (c: Container {id: $container_id})
        ON CREATE SET c.name = $container_name, c.box_range = $box_range_label, 
            c.num_missing = $num_missing

        WITH c
        UNWIND $boxes as box_props
        CREATE (b:Box)
        SET b = box_props

        MERGE (c)-[:CONTAINS]->(b)
        """

        driver.execute_query(
            query,
            container_id=container_id,
            container_name=container_name,
            box_range_label=box_range_label,
            num_missing=num_missing,
            boxes=box_data
        )
        print(f"Successfully loaded Container {container_name} with {len(box_data)} connected boxes!")

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
            REQUIRE n.network_code IS UNIQUE
        """)

        driver.execute_query("""
            CREATE CONSTRAINT station_id_unique
            IF NOT EXISTS FOR (s:Station)
            REQUIRE s.station_code IS UNIQUE
        """)

    station_data = []
    for _, row in stations.iterrows():
        station_dict = {
            "network_code": row['network_code'],
            "station_code": row['station_code'],
            "channel_code": row['channel_code'],
            "location_code": row['location_code'] if row['location_code'] != "--" else None,
            "station_name": row["station_name"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "elevation": row["elevation"],
            "on_date": row['on_date'],
            "off_date": row['off_date'],
            "instrument_depth": row['instrument_depth']
        }

        station_data.append({k: v for k, v in station_dict.items() if v is not None})

    if debug:
        print(station_data[0])

    if not debug:


        query = """
        UNWIND $stations as row

        // merge network node
        MERGE (n:Network {network_code: row.network_code})

        // merge station node
        MERGE (s:Station {station_code: row.station_code})
        ON CREATE SET
            s.station_name = row.station_name,
            s.latitude = row.latitude,
            s.longitude = row.longitude,
            s.elevation = row.elevation
        
        // connect network to station
        MERGE (n)-[:HAS_STATION]->(s)

        // create channel node
        CREATE (c:Channel {
            id: randomUUID(),
            channel_code: row.channel_code,
            location_code: row.location_code,
            on_date: row.on_date,
            off_date: row.off_date,
            instrument_depth: row.instrument_depth
        })

        // link station to channel
        MERGE (s)-[:HAS_CHANNEL]-(c)
        """

        driver.execute_query(query, stations=station_data)
        print(f"Successfully loaded stations, networks, and channels with relationships")
    
    

if __name__=='__main__':
    # Uncomment to load a single excel sheet of box data
    # load_indiv_excel_sheet(
    #     excel_filename="Container FINAL.xlsx", 
    #     sheet_name="1000 - Harry Wood",
    #     debug=False
    # )

    # Uncomment to load the stations
    # load_stations(station_filename="SCEDC Station List FINAL.csv", debug=False)

    print()