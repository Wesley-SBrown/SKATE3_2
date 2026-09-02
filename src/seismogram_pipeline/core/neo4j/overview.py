# src/seismogram_pipeline/core/neo4j/overview.py

from dotenv import load_dotenv
import os
from neo4j import Driver

from .connector import get_driver

load_dotenv()

def get_overview(driver: Driver) -> None:
    """
    Gets an overview of the graph database including node counts, 
    all possible properties per node label, and incoming/outgoing 
    relationships associated with each node type

    Parameters
    ----------
    driver : Driver
        Connector for interfacing with the cloud database
    """

    print("Testing connection...")
    driver.verify_connectivity()
    print("Connected succesfully!")

    print("Nodes:")
    nodes_query = """
    MATCH (n)
    WITH labels(n) AS labels, keys(n) AS keys, n
    UNWIND labels as label
    UNWIND keys as key
    RETURN label as Label, count(DISTINCT n) AS Count, collect(DISTINCT key) AS Properties
    ORDER BY Count DESC
    """

    records, _, _ = driver.execute_query(nodes_query)

    for record in records:
        label = record["Label"] or "Unlabled"
        count = record["Count"]
        properties = ', '.join(record['Properties']) if record['Properties'] else 'None'

        print(f"Node: {label:<20} | Count: {count}")
        print(f" > Properties: {properties}")

    print("\nRelationships:")
    relationships_query = """
    MATCH (n)-[r]->()
    WITH labels(n) as labels, type(r) as relType
    UNWIND labels as label
    RETURN label as Label, 'OUTGOING' as Direction, collect(DISTINCT relType) as Relationships
    UNION
    MATCH ()-[r]-(n)
    WITH labels(n) as labels, type(r) as relType
    UNWIND labels as label
    RETURN label AS Label, 'INCOMING' as Direction, collect(DISTINCT relType) as Relationships
    ORDER BY Label, Direction
    """

    records, _, _ = driver.execute_query(relationships_query)

    current_label = None
    for record in records:
        label = record["Label"]
        direction = record['Direction']
        rels = ', '.join(record['Relationships']) if record['Relationships'] else "None"

        if label != current_label:
            print(f"\nNode: {label}")
            current_label = label
        print(f" > {direction:<9}: {rels}")

    print("\nGlobal Relationship Frequencies:")
    global_rel_q = """
    MATCH ()-[r]-()
    RETURN type(r) AS Type, count(r) AS Count
    ORDER BY Count DESC
    """

    records, _, _ = driver.execute_query(global_rel_q)

    for record in records:
        rel_type = record['Type']
        count = record['Count']
        print(f"Relationship: {rel_type:<25} | Count: {count}") 

if __name__=='__main__':
    driver = get_driver()
    get_overview(driver=driver)
    driver.close()