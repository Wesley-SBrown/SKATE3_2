# src/seismogram_pipeline/core/neo4j/overview.py

from dotenv import load_dotenv
import os
from neo4j import Driver, GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

def get_overview(driver: Driver) -> None:
    """
    Gets an overview of the graph database including nodes & counts,
    relationships & frequencies

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
    RETURN labels(n)[0] AS Label, count(n) AS Count
    ORDER BY Count DESC
    """

    records, _, _ = driver.execute_query(nodes_query)

    for record in records:
        label = record["Label"] or "Unlabled"
        count = record["Count"]

        print(f"Node: {label:<20} | Count: {count}")

    print("\nRelationships:")
    relationships_query = """
    MATCH ()-[r]->()
    RETURN type(r) as Type, count(r) as Count
    ORDER BY Count DESC
    """

    records, _, _ = driver.execute_query(relationships_query)

    for record in records:
        r_type = record["Type"]
        count = record["Count"]
        print(f"Relationship: {r_type:<25} | Count: {count}")

if __name__=='__main__':
    driver = GraphDatabase.driver(uri=URI, auth=(USERNAME, PASSWORD))
    get_overview(driver=driver)
    driver.close()