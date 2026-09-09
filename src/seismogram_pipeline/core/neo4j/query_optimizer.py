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

    query = re.split(r';(?=(?:[^\']*\'[^\']*\')*[^\']*$)(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)', file_contents)[0]

    contents = record_name.split('_')
    
    station = contents[1]
    date = parse_date(contents[6])

    timeStart('get_record')
    cleaned_query = query.strip()
    if not cleaned_query:
        return
    print("Executing query...")
    try:
        timeStart('client_time')
        result = driver.execute_query(cleaned_query, 
                                target_record_name=record_name,
                                date=date,
                                station_code=station
                                )
        client_run_time = timeEnd('client_time')

        summary = result.summary
        server_time = summary.result_available_after + summary.result_consumed_after
        print(f"Server time: {server_time} ms | Client execution time: {client_run_time* 1000:.2f} ms")
        
    except Exception as e:
        print(f"[ERROR] Query execution failed: {e}")

    print(f"Total execution time: {timeEnd("get_record")}")

def retrieve_record_batch(driver: Driver, records: list[str]) -> None:
    # TODO: implement batch record retrieval
    # helps counteract cold start issue
    # testing showed a cut in client execution time by 70ms at the end of a 5 run loop
    # NOTE: caching on AuraDB's side could also contribute to total speed up time 
    ...
    driver.execute_query(batch=records)

if __name__=='__main__':
    driver = get_driver()

    retrieve_record(
        filepath="src/seismogram_pipeline/core/neo4j/queries/optimal_record_query.cypher",
        driver=driver,
        record_name='CI_HAI_LEG_S_H_S_19410628_0902_1'
    )



    

    