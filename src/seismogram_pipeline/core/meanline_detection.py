from .timer import timeStart, timeEnd
from .debug import Debug
from .stats_recorder import Record

from .otsu_threshold_image import otsu_threshold_image
from .hough_lines import get_all_hough_lines
from .quality_control import points_to_rho_theta
from skimage.morphology import remove_small_objects
import numpy as np
import skimage.draw as skidraw
from skimage.color import gray2rgb
import numpy.ma as ma
import geojson
import numpy.typing as npt
from typing import Any

# type aliases for reusability
Point2D = tuple[int, int]
LineEndpoints = tuple[Point2D, Point2D]

def detect_meanlines(
    masked_image: np.ma.MaskedArray, 
    corners: dict[str, tuple[Any, ...]], 
    scale: int = 1, 
    config: dict = None
) -> list[LineEndpoints]:
    """
    Detects and extracts meanlines within a specified ROI of an image

    This function crops the image's region of interest based on the provided coords & padding.
    Otsu's thresholding is then applied and small objects are filtered out
    Hough transform determines the parallel lines (meanlines).

    Parameters
    ----------
    masked_image : MaskedArray
        Input image tranformed into a numpy masked array
    corners : dict[str, tuple[Any, ...]]
        Dictionary of key-defined corners of the image
    scale : int, optional, default 1
        Scaling factor applied to adjust trace spacing, padding, and object size thresholds
    
    Returns
    -------
    line : list[LineEndpoints]
        List of detected lines
    """
    trace_spacing = lambda scale: int(config.get('base_trace_spacing') * scale)
    padding = trace_spacing(scale) / 2

    timeStart("bound image")
    # effectively shrink the roi by a distance **padding**
    top_bound = padding + np.amax([corners["top_left"][1], corners["top_right"][1]])
    bottom_bound = -padding + np.amin(
        [corners["bottom_left"][1], corners["bottom_right"][1]]
    )
    left_bound = padding + np.amax([corners["bottom_left"][0], corners["top_left"][0]])
    right_bound = -padding + np.amin(
        [corners["top_right"][0], corners["bottom_right"][0]]
    )

    # mask all image values outside of this shrunken roi
    bounded_image = masked_image.copy()
    top_bound = int(top_bound)
    bottom_bound = int(bottom_bound)
    left_bound = int(left_bound)
    right_bound = int(right_bound)
    bounded_image[:top_bound, :] = ma.masked
    bounded_image[bottom_bound:, :] = ma.masked
    bounded_image[:, :left_bound] = ma.masked
    bounded_image[:, right_bound:] = ma.masked
    timeEnd("bound image")

    Debug.save_image("meanlines", "bounded_image", bounded_image.filled(0))

    timeStart("threshold image")
    black_and_white_image = otsu_threshold_image(bounded_image)
    timeEnd("threshold image")

    Debug.save_image("meanlines", "thresholded_image", black_and_white_image)

    timeStart("remove small objects")

    # create lambda function for object sizes
    small_object_size = lambda scale: int(config.get("base_small_object_size") * scale * scale)

    filtered_image = remove_small_objects(
        black_and_white_image, max_size=small_object_size(scale) - 1
    )
    timeEnd("remove small objects")

    Debug.save_image("meanlines", "filtered_image", filtered_image)

    timeStart("get hough lines")
    roi_top_angle = np.rad2deg(
        points_to_rho_theta(corners["top_left"], corners["top_right"])[1]
    )
    angle_padding = config.get('angle_padding_deg')  # degrees
    min_angle = roi_top_angle - angle_padding
    max_angle = roi_top_angle + angle_padding
    separation_distance_ratio = config.get("separation_distance_ratio")
    min_separation_distance = int((separation_distance_ratio) * trace_spacing(scale))
    lines = get_all_hough_lines(
        filtered_image,
        min_angle=min_angle,
        max_angle=max_angle,
        min_separation_distance=min_separation_distance,
        min_separation_angle=config.get("min_separation_angle_deg"),
    )
    timeEnd("get hough lines")

    print(f"found {len(lines)} meanlines")
    Record.record("num_meanlines", len(lines))

    if Debug.active:
        debug_image = gray2rgb(np.copy(masked_image))
        line_coords = [
            skidraw.line(line[0][1], line[0][0], line[1][1], line[1][0])
            for line in lines
        ]
        for line in line_coords:
            rr, cc = line
            mask = (
                (rr >= 0)
                & (rr < debug_image.shape[0])
                & (cc >= 0)
                & (cc < debug_image.shape[1])
            )
            debug_image[rr[mask], cc[mask]] = [1.0, 0, 0]
        Debug.save_image("meanlines", "meanlines", debug_image)

    return lines


def meanlines_to_geojson(
    lines: list[LineEndpoints]
) -> geojson.FeatureCollection:
    """"
    Converts a list of meanlines into a geojson FeatureCollection
    
    Parameters
    ----------
    lines: list[LineEndpoints]
        A list of line segments, where each line is represented
        as a tuple of two 2D points ((x1, y1), (x2, y2)).
    
    Returns
    -------
    newFeature : FeatureCollection
        GeoJSON collection of Features containing all the input lines

    """
    lines = [
        geojson.Feature(geometry=geojson.LineString(line), id=idx)
        for idx, line in enumerate(lines)
    ]
    newFeature = geojson.FeatureCollection(lines)
    return newFeature
