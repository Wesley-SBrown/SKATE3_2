# src/seismogram_pipeline/core/neo4j/execute_query.py

import re
from neo4j import Driver

from .connector import get_driver
from ..timer import timeStart, timeEnd

def execute_cypher(filepath: str, driver: Driver, **query_params) -> None:
    """
    Executes Cypher query from specified file
    """

    with open(file=filepath, mode='r', encoding='utf-8') as f:
        file_contents = f.read()

    # ensure connectivity
    driver.verify_connectivity()

    queries = re.split(r';(?=(?:[^\']*\'[^\']*\')*[^\']*$)(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)', file_contents)

    timeStart("query")
    for query in queries:
        cleaned_query = query.strip()
        if not cleaned_query:
            continue

        print("Executing query...")
        try:
            print(driver.execute_query(query, **query_params))
        except Exception as e:
            print(f"Query execution failed: {e}")
    print(f"Execution time: {timeEnd("query")}")

if __name__=='__main__':
    driver = get_driver()

    file_path = "src/seismogram_pipeline/core/neo4j/queries/testing_queries.cypher"

    record_name = "CI_HAI_LEG_S_H_S_19410628_0902_2"
    contents = record_name.split('_')
        
    station = contents[1]
    execute_cypher(filepath=file_path, driver=driver, target_record_name=record_name,
                   station_code=station)