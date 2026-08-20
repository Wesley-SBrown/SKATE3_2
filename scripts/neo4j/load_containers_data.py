# scripts/neo4j/load_containers_data.py

import os
import uuid
from dotenv import load_dotenv
import pandas as pd
from neo4j import GraphDatabase, Driver
from src.seismogram_pipeline.core.neo4j.connector import get_driver


def load_indiv_excel_sheet():
    # define cols for sheet (may change per sheet)
    cols = ['verified_by', 'box_num', 'stack_num', 'from_year',
            'from_month', 'from_day', 'through_year', 'through_month', "through_day",
            'exceptions', 'notes', 'prev_no', 'comments', 'image_name', 'checked_out',
            'name', 'scanned_date', 'scanned_by']

    # define range of cols to select
    cols_to_save = list(range(len(cols)))

    # select single sheet from excel file
    harry_wood = pd.read_excel("data/inputs/Container FINAL.xlsx", 
                            sheet_name="1000 - Harry Wood", skiprows=2,
                            header=None, names=cols, usecols=cols_to_save)
    
    # print(harry_wood.iloc[0, 5:])
    
    num_missing = int(harry_wood.tail(1)["box_num"].values[0])
    harry_wood = harry_wood[:-2]
    harry_wood["box_num"] = pd.to_numeric(harry_wood["box_num"], errors="coerce")
    harry_wood = harry_wood.dropna(subset=["box_num"])

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
    harry_wood["from_date"] = harry_wood.apply(lambda r: build_date(r, "from"), axis=1)
    harry_wood["through_date"] = harry_wood.apply(lambda r: build_date(r, "through"), axis=1)

    # print(harry_wood.info())
    # print(harry_wood.tail(10))
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

    # Create HarryWood container node
    container_id = str(uuid.uuid4())
    container_name = "Harry Wood"
    box_range_label = "1000"

    box_data = []
    for _, row in harry_wood.iterrows():
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
    print(f"Successfully loaded Container 'Harry Wood' with {len(box_data)} connected boxes!")


if __name__=='__main__':
    load_indiv_excel_sheet()



    


