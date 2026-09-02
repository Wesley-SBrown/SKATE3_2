# src/seismogram_pipeline/core/neo4l/query_optimizer.py

import re
from neo4j import Driver

from .connector import get_driver
from ..timer import timeStart, timeEnd

def retrieve_record(filepath: str, driver: Driver, record_name: str) -> None:
    """
    Optimize record retrieval query by determining the correct box first 
    """
    from .utils.parsers import parse_date

    with open(filepath, 'r', encoding='utf-8') as f:
        file_contents = f.read()

    driver.verify_connectivity()

    queries = re.split(r';(?=(?:[^\']*\'[^\']*\')*[^\']*$)(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)', file_contents)


    timeStart('get_record')
    contents = record_name.split('_')
    
    # record_type = None
    # pier = None
    # if '.' in contents[2]:
    #     record_type, pier = contents[2].split(".")

    date = parse_date(contents[6])

    for query in queries:
        cleaned_query = query.strip()
        if not cleaned_query:
            continue
        print("Executing query...")
        try:
            print(driver.execute_query(cleaned_query, 
                                       target_record_name=record_name,
                                       date=date
                        )
            )
        except Exception as e:
            print(f"[ERROR] Query execution failed: {e}")

    print(f"Execution time: {timeEnd("get_record")}")


if __name__=='__main__':
    driver = get_driver()

    retrieve_record(
        filepath="src/seismogram_pipeline/core/neo4j/queries/optimal_record_query.cypher",
        driver=driver,
        record_name='CI_HAI_LEG_S_H_S_19410628_0902_2'
    )



    

    