# scripts/neo4j/load_data.py

from PIL import Image

from src.seismogram_pipeline.core.neo4j.connector import get_driver
from src.seismogram_pipeline.core.neo4j.stations import load_stations
from src.seismogram_pipeline.core.neo4j.excel import load_indiv_excel_sheet   
from src.seismogram_pipeline.core.neo4j.records import (
    save_box_locally, load_box_from_cache
)
from src.seismogram_pipeline.core.neo4j.utils.imaging import inspect_tiff_metadata
from src.seismogram_pipeline.core.verify_network import verify_and_access_share


if __name__=='__main__':
    # Uncomment to load a single excel sheet of box data
    # load_indiv_excel_sheet(
    #     excel_filename="Container FINAL.xlsx", 
    #     sheet_name="2000-3000 - Hugo Benioff",
    #     debug=False
    # )

    # Uncomment to load the stations
    # load_stations(station_filename="SCEDC Station List FINAL.csv", debug=False)

    # Uncomment to save a box's record metadata locally
    # Image.MAX_IMAGE_PIXELS = None
    # save_box_locally(box_filename="Box 1474", debug=False)

    # Uncomment to load a box's records from cache into Neo4J
    # load_box_from_cache(box_num=2848)

    pass