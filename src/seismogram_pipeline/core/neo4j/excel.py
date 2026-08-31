# src/seismogram_pipeline/core/neo4j/excel.py

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
    cols = ['verified_by', 'box_count', 'box_num', 'stack_num', 'from_year',
            'from_month', 'from_day', 'through_year', 'through_month', "through_day",
            'exceptions', 'notes', 'comments', 'prev_no', 'image_name', 'scanned_date',
            'scanned_by', 'checked_out', 'name'
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

        driver.execute_query("""
            CREATE INDEX box_num_idx
            IF NOT EXISTS FOR (b:Box)
            ON (b.boxNum)
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
            "boxNum": int(row["box_num"]),
            "stackNum": int(row["stack_num"]) if pd.notna(row["stack_num"]) else None,
            "fromDate": row["from_date"],
            "throughDate": row["through_date"],
            "exceptions": row["exceptions"] if pd.notna(row["exceptions"]) else None,
            "notes": row["notes"] if pd.notna(row["notes"]) else None,
            "prevNo": row["prev_no"] if pd.notna(row["prev_no"]) else None,
            "comments":row["comments"] if pd.notna(row["comments"]) else None,
            "imageName": row["image_name"] if pd.notna(row["image_name"]) else None,
            "checkedOut": row["checked_out"] if pd.notna(row["checked_out"]) else None,
            "name": row["name"] if pd.notna(row["name"]) else None,
            "scannedDate": row["scanned_date"] if pd.notna(row["scanned_date"]) else None,
            "scannedBy": row["scanned_by"] if pd.notna(row["scanned_by"]) else None
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
        driver.close()

        print(f"Successfully loaded Container {container_name} with {len(box_data)} connected boxes!")