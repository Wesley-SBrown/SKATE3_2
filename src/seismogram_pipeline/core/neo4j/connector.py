# src/seismogram_pipeline/core/neo4j/connector.py

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase, Driver

# load .env vars into memory
load_dotenv()

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")
AUTH = (USERNAME, PASSWORD)

def get_driver(uri: str = None, auth: tuple[str,str] = (None, None)) -> Driver:
    if uri is None or auth is None:
        load_dotenv()
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USERNAME")
        pwd = os.getenv("NEO4J_PASSWORD")
        auth = (user, pwd)

    return GraphDatabase.driver(uri=uri, auth=auth)

if __name__=='__main__':
    driver = get_driver(uri=URI, auth=AUTH)
    driver.verify_connectivity()
    print("AuraDB connected successfully!")

    with driver.session() as session:
        output = session.run("RETURN 'Test' AS message")
        print(output.single()['message'])

    driver.close()