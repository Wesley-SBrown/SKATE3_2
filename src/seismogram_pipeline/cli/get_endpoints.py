# -*- coding: utf-8 -*-
"""
Description:
  Calculates the endpoints in a seismogram.

Usage:
  get_endpoints.py --segments <filename> [--output <filename>]
  get_endpoints.py -h | --help

Options:
  -h --help              Show this screen.
  --segments <filename>  Filename of geojson segments.
  --output <filename>    Filename of geojson output.
"""

from docopt import docopt


def get_endpoints(segments_file: str, out_file: str) -> None:
    """
    Processes the segments file to extract and write endpoints

    Parameters
    ----------
    segments_file: str
        Input segments file path
    out_file: str
        Output endpoints file path
    """
    
    from ..core.geojson_io import get_features
    from ..core.endpoints import (
        get_endpoint_data,
        generate_geojson,
        write_geojson,
        write_csv,
    )
    import yaml
    from pathlib import Path

    CONFIG_PATH = (Path(__file__)
        .resolve()
        .parents[3]
        / "config.yaml"
    )

    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)['storage']

    storage_config = config.get('storage', {})
    pipeline_outputs = storage_config.get("pipeline_outputs")

    outputs_dir = storage_config.get("outputs_dir", "data/outputs")

    segments_path = (Path(__file__)
                     .resolve()
                     .parents[3]
                     .joinpath(outputs_dir, segments_file)
    )

    features = get_features(filename=segments_path)
    data = get_endpoint_data(features=features)
    
    if out_file is None:
        out_file = pipeline_outputs.get("endpoints")

    out_path = (Path(__file__)
                .resolve()
                .parents[3]
                .joinpath(outputs_dir, out_file)
    )
    
    write_geojson(out_path, generate_geojson(data))


def main():
    """Main entry point for the get_endpoints CLI."""
    arguments = docopt(__doc__)
    segments_file = arguments["--segments"]
    out_file = arguments["--output"]

    if segments_file:
        get_endpoints(segments_file=segments_file, out_file=out_file)
    else:
        print(arguments)


if __name__ == "__main__":
    main()
