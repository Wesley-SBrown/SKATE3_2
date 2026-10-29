# scripts/neo4j/load_data.py

import argparse
from PIL import Image

from src.seismogram_pipeline.core.neo4j.stations import load_stations
from src.seismogram_pipeline.core.neo4j.excel import load_indiv_excel_sheet   
from src.seismogram_pipeline.core.neo4j.records import (
    save_box_locally, load_box_from_cache
)


def main():
    parser = argparse.ArgumentParser(description="Data loading and management CLI tool.")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # 1) loading in an excel sheet
    p_excel = subparsers.add_parser("load-excel", help="Load a single excel sheet of box data")
    p_excel.add_argument("--excel-filename", default="Container FINAL.xlsx", help="Excel filepath")
    p_excel.add_argument("--sheet-name", default="2000-3000 - Hugo Benioff", help="Excel sheet filename")
    p_excel.add_argument("--debug", action="store_true", help="Enable debug mode")

    # 2) loading in stations
    p_stations = subparsers.add_parser("load-stations", help="Load the station list CSV")
    p_stations.add_argument("--station-filename", default="SCEDC Station List FINAL.csv", 
                            help="Station CSV filepath")
    p_stations.add_argument("--debug", action="store_true", help="Enable debug mode")

    # 3) box local download
    p_save = subparsers.add_parser("save-box", help="Save a box's record metadata locally")
    p_save.add_argument("--box-filename", default="Box 2818", help="Box filename")
    p_save.add_argument("--debug", action="store_true", help="Enable debug mode")

    # 4) upload local box to Neo4J
    p_cache = subparsers.add_parser("load-cache", help="Load a box's records from cache into Neo4J")
    p_cache.add_argument("--box-num", default="2845", help="Box number")

    args = parser.parse_args()

    # dynamic execuition based on subcommand
    if args.command == "load-excel":
        load_indiv_excel_sheet(
            excel_filename=args.excel_filename,
            sheet_name=args.sheet_name,
            debug=args.debug
        )
    elif args.command == "load-stations":
        load_stations(
            station_filename=args.station_filename,
            debug=args.debug
        )
    elif args.command == "save-box":
        Image.MAX_IMAGE_PIXELS = None
        save_box_locally(
            box_filename=args.box_filename,
            debug=args.debug
        )
    elif args.command == "load-cache":
        load_box_from_cache(
            box_num=args.box_num
        )

if __name__ == '__main__':
    main()

