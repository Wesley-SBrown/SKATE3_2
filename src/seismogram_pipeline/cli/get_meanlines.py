"""
Description:
  Given a grayscale seismogram and a geojson Polygon feature
  representing the seismogram's region-of-interest, estimates
  the meanlines of the seismogram data, and saves as a geojson
  FeatureCollection of features with LineString geometries.

Usage:
  get_meanlines.py --roi <filename> --image <filename> --output <filename> [--scale <scale>] [--debug <directory>]
  get_meanlines.py -h | --help

Options:
  -h --help            Show this screen.
  --roi <filename>     Filename of geojson Polygon representing region-of-interest.
  --image <filename>   Filename of grayscale seismogram.
  --output <filename>  Filename of geojson output.
  --scale <scale>      1 for a full-size seismogram, 0.25 for quarter-size, etc. [default: 1]
  --debug <directory>  Save intermediate steps as images for inspection in <directory>.

"""
import yaml
from docopt import docopt
from typing import Union
from pathlib import Path

def get_meanlines(
    in_file: str, out_file: str, roi_file: str,
    scale: float = 1, debug_dir: Union[str, bool] = False
) -> None:
    """
    Process grayscale image and region of interest and write meanlines

    Parameters
    ----------
    in_file: str
        Input grayscale seismogram file path
    out_file: str
        Output geojson file path
    roi_file: str
        Region of interest geojson file path
    scale: float, default 1
        Image scale factor
    debug_dir: str | bool, default False
        Flag whether to save intermediate images
    """

    CONFIG_PATH = (Path(__file__)
        .resolve()
        .parents[3]
        / "config.yaml"
    )

    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)

    storage_config = config.get('storage', {})
    pipeline_settings = config.get('pipeline_settings', {})

    inputs_dir = storage_config.get("inputs_dir", "data/inputs")
    outputs_dir = storage_config.get("outputs_dir", "data/outputs")

    if isinstance(debug_dir, str):
        from ..core.dir import ensure_dir_exists

        ensure_dir_exists(debug_dir)

    from ..core.debug import Debug

    if isinstance(debug_dir, str):
        Debug.set_directory(debug_dir)

    from ..core.timer import timeStart, timeEnd
    from ..core.load_image import get_image
    from ..core.geojson_io import get_features, save_features
    from ..core.polygon_mask import mask_image
    from ..core.meanline_detection import detect_meanlines, meanlines_to_geojson
    from ..core.roi_detection import geojson_to_corners

    timeStart("get meanlines")

    timeStart("read image")
    input_path = (
        Path(__file__)
            .resolve()
            .parents[3]
            .joinpath(inputs_dir, in_file)
    )
    image = get_image(input_path)
    timeEnd("read image")

    roi_path = (
        Path(__file__)
            .resolve()
            .parents[3]
            .joinpath(outputs_dir, roi_file)
    )

    roi_features = get_features(roi_path)
    roi_polygon = roi_features["geometry"]["coordinates"][0]

    corners = geojson_to_corners(roi_features)

    timeStart("mask image")
    masked_image = mask_image(image, roi_polygon)
    timeEnd("mask image")

    meanlines = detect_meanlines(
        masked_image, 
        corners=corners, 
        scale=scale,
        config=pipeline_settings.get("meanline_detection")
    )

    timeStart("convert to geojson")
    meanlines_as_geojson = meanlines_to_geojson(meanlines)
    timeEnd("convert to geojson")

    # config default fallback
    if not out_file:
        out_file = storage_config.get('pipeline_outputs', {}).get('meanlines', 'meanlines.json')

    output_path = (
        Path(__file__)
            .resolve()
            .parents[3]
            .joinpath(outputs_dir, out_file)
    )

    timeStart("saving as geojson")
    save_features(meanlines_as_geojson, output_path)
    timeEnd("saving as geojson")

    timeEnd("get meanlines")


def main():
    """Main entry point for the get_meanlines CLI."""
    arguments = docopt(__doc__)
    in_file = arguments["--image"]
    roi_file = arguments["--roi"]
    out_file = arguments["--output"]
    scale = float(arguments["--scale"])
    debug_dir = arguments["--debug"]

    if in_file and roi_file:
        get_meanlines(in_file, out_file, roi_file, scale, debug_dir)
    else:
        print(arguments)


if __name__ == "__main__":
    main()
