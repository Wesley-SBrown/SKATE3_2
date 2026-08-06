"""
Description:
  Calculates the intersections in a grayscale seismogram image.

Usage:
  get_intersections.py --image <filename> --roi <filename> [--output <filename>] [--scale <scale>] [--debug <directory>]
  get_intersections.py -h | --help

Options:
  -h --help            Show this screen.
  --image <filename>   Filename of grayscale input image.
  --roi <filename>     Filename of geojson roi.
  --output <filename>  Filename of geojson output.
  --scale <scale>      1 for a full-size seismogram, 0.25 for quarter-size, etc. [default: 1]
  --debug <directory>  Save intermediate steps as images for inspection in <directory>.

"""

import os, yaml
from docopt import docopt
from typing import Union
from pathlib import Path


def get_intersections(
    in_file: str, roi_file: str, out_file: str, 
    scale: int = 1, debug_dir: Union[str, bool] = False
) -> None:
    """
    Process grayscale image & region of interest and write intersections

    Parameters
    ----------
    in_file: str
        Grayscale seismogram image filepath
    roi_file: str
        Region of interest geojson filepath
    out_file: str
        Output file path
    scale: float, default 1 (unused)
        Image scale factor
    debug_dir: str | bool, default False
        Flag whether to save intermediate images

    """
    # TODO: implement scale resizing
    CONFIG_PATH = (Path(__file__)
        .resolve()
        .parents[3]
        / "config.yaml"
    )

    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)['storage']

    storage_config = config.get('storage', {})
    pipeline_settings = config.get('pipeline_settings', {})

    inputs_dir = storage_config.get("inputs_dir", "data/inputs")
    outputs_dir = storage_config.get("outputs_dir", "data/outputs")

    # guards against accidental True value passing check
    if isinstance(debug_dir, str):
        from ..core.dir import ensure_dir_exists

        ensure_dir_exists(debug_dir)

    from ..core.timer import timeStart, timeEnd
    from ..core.intersection_detection import find_intersections
    from ..core.load_image import get_image
    from ..core.geojson_io import get_features
    from ..core.polygon_mask import mask_image
    from ..core.geojson_io import save_features
    from skimage.io import imsave

    timeStart("get intersections")

    timeStart("read image")
    input_path = (Path(__file__)
                  .resolve()
                  .parents[3]
                  .joinpath(inputs_dir, in_file)
    )
    grayscale_image = get_image(input_path)
    timeEnd("read image")

    roi_path = (
            Path(__file__)
                .resolve()
                .parents[3]
                .joinpath(outputs_dir, roi_file)
        )
    

    roi_polygon = get_features(roi_path)["geometry"]["coordinates"][0]

    timeStart("mask image")
    masked_image = mask_image(grayscale_image, roi_polygon)
    timeEnd("mask image")

    intersections = find_intersections(masked_image.filled(False), figure=False) # TODO: add `scale` parameter

    # if target file missing, fall back on config default
    if not out_file:
        out_path = (Path(__file__)
                    .resolve()
                    .parents[3]
                    .joinpath(
                        outputs_dir,
                        storage_config["pipeline_config"]["intersections"]
                    )
        )
    else:
        out_path = (Path(__file__)
                    .resolve()
                    .parents[3]
                    .joinpath(
                        outputs_dir,
                        out_file
                    )
        )

    timeStart("saving to " + str(out_path))
    intersections_as_geojson = intersections.asGeoJSON()
    save_features(intersections_as_geojson, out_path)
    timeEnd("saving to " + str(out_path))

    if isinstance(debug_dir, str):
        # safe platform-agnositc path combining 
        debug_filename = storage_config["pipeline_outputs"].get('intersections_raster', "intersections.png")
        debug_filepath = os.path.join(debug_dir, debug_filename)
        timeStart("saving to " + debug_filepath)
        intersections_as_image = intersections.asImage().astype(float)
        imsave(debug_filepath, intersections_as_image)
        timeEnd("saving to " + debug_filepath)

    timeEnd("get intersections")


def main():
    """Main entry point for the get_intersections CLI."""
    arguments = docopt(__doc__)
    in_file = arguments["--image"]
    roi_file = arguments["--roi"]
    out_file = arguments["--output"]
    debug_dir = arguments["--debug"]
    scale = float(arguments["--scale"]) if arguments["--scale"] else 1

    if in_file and out_file:
        get_intersections(in_file, roi_file, out_file, scale, debug_dir)
    else:
        print(arguments)


if __name__ == "__main__":
    main()
