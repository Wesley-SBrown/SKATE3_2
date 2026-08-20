# src/seismogram_pipeline/core/neo4j/clear_graph.py

from neo4j import GraphDatabase, Driver
from dotenv import load_dotenv
import os

load_dotenv()

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

def clear_graph(driver: Driver) -> None:
    """
    Completely clears the AuraDB graph
    - mainly used for testing

    Parameters
    ----------
    driver : Driver
        Connector for interfacing with the cloud database
    """

    driver.verify_connectivity()
    print("Connected to AuraDB")
    query = """
    MATCH (n)
    DETACH DELETE n
    """
    with driver.session() as session:
        session.run(query)
        print("Graph cleared successfully")


if __name__=='__main__':
    driver = GraphDatabase.driver(uri=URI, auth=(USERNAME, PASSWORD))
    clear_graph(driver)
    driver.close()