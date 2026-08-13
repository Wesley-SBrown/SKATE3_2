# -*- coding: utf-8 -*-
"""
Description:
  Assigns segments to meanlines in a seismogram.

Usage:
  get_segment_assignments.py --segments <filename> --meanlines <filename> [--output <filename>]
  get_segment_assignments.py -h | --help

Options:
  -h --help              Show this screen.
  --segments <filename>  Filename of geojson segments.
  --meanlines <filename> Filename of geojson meanlines.
  --output <filename>    Filename of json output.

"""
from docopt import docopt
from pathlib import Path
import yaml


def get_segment_assignments(
        segments_file: str, meanlines_file: str, out_file: str) -> None:
    """
    Process the segments and meanlines files to extract and write segment assignments

    Parameters
    ----------
    segments_file: str
        Input segments filename
    meanlines_file: str
        Input meanlines filename
    out_file: str
        Output segment assignments filename
    """

    from ..core.geojson_io import get_features
    from ..core.timer import timeStart, timeEnd
    from ..core.endpoints import get_endpoint_data, generate_geojson
    from ..core.segment_assignment import (
        assign_segments_to_meanlines,
        save_assignments_as_json,
    )

    timeStart("get segment assignments")

    CONFIG_PATH = (Path(__file__)
        .resolve()
        .parents[3]
        / "config.yaml"
    )

    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)['storage']

    storage_config = config.get('storage', {})

    pipeline_settings = config.get('pipeline_settings', {})

    asmts_cfg = pipeline_settings.get("segment_assignment", {})

    outputs_dir = storage_config.get("outputs_dir", "data/outputs")

    timeStart("read segments")
    segments_path = (Path(__file__)
                     .resolve()
                     .parents[3]
                     .joinpath(outputs_dir, segments_file)
    )
    segments_features = get_features(filename=segments_path)
    timeEnd("read segments")

    timeStart("compute endpoint stats")
    endpoint_data = get_endpoint_data(features=segments_features)
    segments_geojson = generate_geojson(endpoint_data)
    timeEnd("compute endpoint stats")

    timeStart("read meanlines")
    meanlines_path = (Path(__file__)
                      .resolve()
                      .parents[3]
                      .joinpath(outputs_dir, meanlines_file)
    )
    meanlines_features = get_features(filename=meanlines_path)
    timeEnd("read meanlines")

    # assign segments to their associated meanlines
    timeStart("segment assignment")
    assignments = assign_segments_to_meanlines(
        segments=segments_features,
        meanlines=meanlines_features,
        segment_data=segments_geojson,
        max_search_dist=asmts_cfg.get("dist"),
        max_overlap=asmts_cfg.get("max_overlap"),
        max_save_dist=asmts_cfg.get("max_save_dist"),
        base_timing_spacing=asmts_cfg.get("base_timing_spacing"),
        min_timing_slope_dist=asmts_cfg.get("min_timing_slope_dist"),
        max_timing_slope_dist=asmts_cfg.get("max_timing_slope_dist"),
        max_coord_length=asmts_cfg.get("max_coord_length"),
        max_sd=asmts_cfg.get("max_sd"),
        max_coord_search=asmts_cfg.get("max_coord_search"),
        tolerance_window=asmts_cfg.get("tolerance_window"),
        min_hits=asmts_cfg.get("min_hits")
    )
    timeEnd("segment assignment")

    # save to ouput JSON file
    out_path = (Path(__file__)
                .resolve()
                .parents[3]
                .joinpath(outputs_dir, out_file)
    )
    save_assignments_as_json(data=assignments, filepath=out_path)

    timeEnd("get segment assignments")


def main():
    """Main entry point for the get_segment_assignments CLI."""
    arguments = docopt(__doc__)
    segments_file = arguments["--segments"]
    meanlines_file = arguments["--meanlines"]
    out_file = arguments["--output"]

    if segments_file and meanlines_file:
        get_segment_assignments(segments_file, meanlines_file, out_file)
    else:
        print(arguments)


if __name__ == "__main__":
    main()
