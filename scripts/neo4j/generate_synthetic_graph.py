# srcipts/neo4j/generate_synthetic_graph.py

import os
import uuid
import random
from neo4j import Driver
from faker import Faker
from dotenv import load_dotenv
from datetime import timedelta, date
from src.seismogram_pipeline.core.neo4j.connector import get_driver

class CDWPDataGenerator:
    def __init__(
        self, driver: Driver,
        batch_size: int = 10
    ) -> None:
        self.driver = driver
        self.faker = Faker()
        self.batch_size = batch_size

    def close(self) -> None:
        self.driver.close()

    def create_contraints(self) -> None:
        """
        Create data contraints before generation
        """

        with self.driver.session() as session:
            session.run(
                "CREATE CONSTRAINT cdwp_location_id_unique " \
                "IF NOT EXISTS FOR (cl:CDWPLocation) " \
                "REQUIRE cl.id IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT cdwp_image_id_unique " \
                "IF NOT EXISTS FOR (ci:CDWPImage) " \
                "REQUIRE ci.cdwp_image_id IS UNIQUE"
            )
    
    def generate_CDWP_locations(self, count: int) -> list[str]:
        """
        Generates CDWPLocation nodes
        """

        query = """
        UNWIND $batch AS row
        CREATE (cl:CDWPLocation {
            id: row.id,
            box_id: row.box_id,
            start_date: date(row.start_date),
            end_date: date(row.end_date),
            container: row.container,
            stack: row.stack,
            previous_no: row.previous_no,
            exceptions: row.exceptions,
            CDWP_location_notes: row.cdwp_location_notes
        })
        """
        batch = []
        location_ids = []

        for _ in range(count):
            location_id = str(uuid.uuid4())
            location_ids.append(location_id)

            start = self.faker.date_between(
                start_date=date(1920,1,1), 
                end_date=date(1990,12,31)
            )
            end = start + timedelta(days=random.randint(1, 30))
            
            batch.append({
                "id": location_id,
                "box_id": random.randint(2000, 2999),
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "container": self.faker.word().upper(),
                "stack": random.randint(1, 60),
                "previous_no": random.randint(0, 50),
                "exceptions": self.faker.sentence() if random.random() > 0.7 else None,
                "cdwp_location_notes": self.faker.text(max_nb_chars=100) if random.random() > 0.7 else None
            })
            
            if len(batch) >= self.batch_size:
                self._execute_write(query, batch)
                batch = []
        
        if batch:
            self._execute_write(query, batch)

        return location_ids

    def generate_CDWP_images(
        self, 
        image_count: int, 
        existing_location_ids: list
    ) -> None:
        """
        Generates CDWP images & matches to CDWPLocations via cdwp_location_id
        """
        query = """
        UNWIND $batch as row
        MATCH (cl:CDWPLocation {id: row.cdwp_location_id})
        CREATE (ci:CDWPImage {
            CDWP_image_id: row.cdwp_image_id,
            PID: row.pid,
            station_code_local: row.station_code_local,
            start_time_correction: date(row.start_time_correction),
            end_time_correction: date(row.end_time_correction),
            side: row.side,
            instrument_name: row.instrument_name,
            t0: row.t0,
            tg: row.tg,
            filename: row.filename,
            CDWP_image_creator: row.cdwp_image_creator
        })
        CREATE (ci)-[:RECORDED_AT]->(cl)
        """
        batch = []
        for i in range(1, image_count + 1):
            start_corr = self.faker.date_between(
                start_date=date(1920, 1, 1),
                end_date=date(1990, 12, 31)
            )
            end_corr = start_corr + timedelta(days=random.randint(0, 3))

            batch.append({
                "cdwp_image_id": i,
                "pid": random.randint(1000, 9999),
                "cdwp_location_id": random.choice(existing_location_ids),
                "station_code_local": f"STN-{random.randint(10, 99)}",
                "start_time_correction": start_corr.isoformat(),
                "end_time_correction": end_corr.isoformat(),
                "side": random.choice(["1", "o", "unknown"]),
                "instrument_name": random.choice(["Sensor-A", "Sensor-B", "Instrument-C"]),
                "t0": round(random.uniform(0.0, 10.0), 4),
                "tg": round(random.uniform(10.0, 50.0), 4),
                "filename": self.faker.file_name(extension="jpg"),
                "cdwp_image_creator": self.faker.name()
            })
            
            if len(batch) >= self.batch_size:
                self._execute_write(query, batch)
                batch = []
                
        if batch:
            self._execute_write(query, batch)

    def _execute_write(self, query, batch):
        with self.driver.session() as session:
            session.execute_write(lambda tx: tx.run(query, batch=batch))


if __name__=='__main__':
    load_dotenv()

    URI = os.getenv("NEO4J_URI")
    USERNAME = os.getenv("NEO4J_USERNAME")
    PASSWORD = os.getenv("NEO4J_PASSWORD")

    driver = get_driver(uri=URI, auth=(USERNAME, PASSWORD))

    generator = None
    try:
        driver.verify_connectivity()
        print("Connected to AuraDB")

        generator = CDWPDataGenerator(driver=driver)

        print("Defining constrinats...")
        generator.create_contraints()

        print("Creating CDWP location nodes...")
        location_ids = generator.generate_CDWP_locations(count=20)
        print(f"Created {len(location_ids)} locations")

        print("Create CDWP image nodes & connections...")
        generator.generate_CDWP_images(image_count=50, existing_location_ids=location_ids)
        print("Created & connected image nodes")

    except Exception as e:
        print(f"[ERROR] Failed to create nodes and relationships: {e}")

    finally:
        if generator:  # Only close if it exists
            generator.close()
            print("AuraDB connection closed")
        else:
            driver.close()
            print("Driver connection closed")