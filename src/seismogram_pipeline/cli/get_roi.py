"""
Description:
  Calculates the corners of the region of interest in a grayscale
  seismogram image.

Usage:
  get_roi.py --image <filename> [--output <filename>] [--scale <scale>] [--debug <directory>]
  get_roi.py -h | --help

Options:
  -h --help            Show this screen.
  --image <filename>   Filename of grayscale input image.
  --output <filename>  Filename of geojson output.
  --scale <scale>      1 for a full-size seismogram, 0.25 for quarter-size, etc. [default: 1]
  --debug <directory>  Save intermediate steps as images for inspection in <directory>.

"""
from docopt import docopt
from typing import Union
import yaml
from pathlib import Path

def get_roi(
    in_file: str, out_file: str, 
    scale: float = 1, debug_dir: Union[str, bool] = False
) -> None:
    """
    Process grayscale image and write region of interest

    Parameters
    ----------
    in_file: str
        Grayscale seismogram image file path
    out_file: str
        Output file path
    scale: int, default 1 (unused)
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

    from ..core.timer import timeStart, timeEnd
    from ..core.load_image import get_image
    from ..core.roi_detection import get_roi as core_roi, corners_to_geojson
    from ..core.geojson_io import save_features

    timeStart("ROI")

    timeStart("read image")
    input_path = (
        Path(__file__)
        .resolve()
        .parents[3]
        .joinpath(inputs_dir, in_file)

    )
    image = get_image(input_path)
    timeEnd("read image")

    corners = core_roi(
        image, scale=scale,
        config=pipeline_settings.get("roi_detection"))

    timeStart("convert to geojson")
    corners_as_geojson = corners_to_geojson(corners)
    timeEnd("convert to geojson")

    if isinstance(debug_dir, str):
        from ..core.polygon_mask import mask_image
        from scipy import misc

        roi_polygon = corners_as_geojson["geometry"]["coordinates"][0]
        timeStart("mask image")
        masked_image = mask_image(image, roi_polygon)
        timeEnd("mask image")
        misc.imsave(debug_dir + "/masked_image.png", masked_image.filled(0))

    if out_file:
        roi_file = (
            Path(__file__)
            .resolve()
            .parents[3]
            .joinpath(outputs_dir, out_file)
        )

        timeStart("saving as geojson")
        save_features(corners_as_geojson, roi_file)
        timeEnd("saving as geojson")
    else:
        print(corners_as_geojson)

    timeEnd("ROI")


def main():
    """Main entry point for the get_roi CLI."""
    arguments = docopt(__doc__)
    in_file = arguments["--image"]
    out_file = arguments["--output"]
    scale = float(arguments["--scale"])
    debug_dir = arguments["--debug"]

    if in_file:
        get_roi(in_file, out_file, scale, debug_dir)
    else:
        print(arguments)


if __name__ == "__main__":
    main()
