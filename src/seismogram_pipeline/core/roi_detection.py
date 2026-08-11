from .timer import timeStart, timeEnd
from .debug import Debug
from .stats_recorder import Record

import numpy as np
from numpy.typing import NDArray
from typing import Union, Any
import cv2
from skimage.filters import threshold_otsu
from skimage.morphology import disk
from skimage.segmentation import find_boundaries
from scipy.ndimage import label
from skimage.transform import hough_line, hough_line_peaks, probabilistic_hough_line
import skimage.draw as skidraw
from skimage.color import gray2rgb

from typing import Optional
from .line_intersection import seg_intersect
from .hough_lines import get_best_hough_lines
from .otsu_threshold_image import otsu_threshold_image

import matplotlib.pyplot as plt
import geojson

def get_boundary(
    grayscale_image: NDArray[np.generic], 
    scale: int = 1, 
    base_trace_width: int = 17
) -> NDArray[np.bool_]:
    """
    Extract the boundary of the largest connected region of interest from a grayscale image 
    using thresholding, morphological operations, and component labeling
    
    Parameters
    ----------
    grayscale_image : NDArray[np.generic]
        The input grayscale image to be processed.
    scale : int, optional, default 1
        A scaling factor applied to the base trace width for the morphological operator
    base_trace_width : int, optional, default 17
        The baseline width used for creating the disk-shaped structuring element

    Returns
    -------
    region_of_interest_boundary : NDArray[np.bool_]
        A boolean array containing the extracted boundary of the largest identified region of interest
    """
    timeStart("threshold image")
    black_and_white_image = otsu_threshold_image(grayscale_image)
    timeEnd("threshold image")

    Debug.save_image("roi", "black_and_white_image", black_and_white_image)

    timeStart("morphological open image")
    trace_width = lambda scale: int(base_trace_width * scale)
    filter_element_opening = disk(trace_width(scale))
    opened_image = cv2.morphologyEx(
        255 * black_and_white_image.astype(np.uint8),
        cv2.MORPH_OPEN,
        filter_element_opening,
    )
    timeEnd("morphological open image")

    Debug.save_image("roi", "opened_image", opened_image)

    timeStart("invert image")
    opened_image = np.invert(opened_image)
    timeEnd("invert image")

    timeStart("segment image into connected regions")
    labeled_components, num_components = label(opened_image)
    timeEnd("segment image into connected regions")

    timeStart("calculate region areas")
    # Have to cast to np.intp with ndarray.astype because of a numpy bug
    # see: https://github.com/numpy/numpy/pull/4366
    areas = np.bincount(labeled_components.flatten().astype(np.intp))[1:]
    timeEnd("calculate region areas")

    timeStart("calculate region boundaries")
    image_boundaries = find_boundaries(
        labeled_components, connectivity=1, mode="inner", background=0
    )
    timeEnd("calculate region boundaries")

    Debug.save_image("roi", "image_boundaries", image_boundaries)

    timeStart("mask region of interest")
    largest_component_id = np.argmax(areas) + 1
    region_of_interest_mask = labeled_components != largest_component_id
    region_of_interest_boundary = np.copy(image_boundaries)
    region_of_interest_boundary[region_of_interest_mask] = 0
    timeEnd("mask region of interest")

    Debug.save_image("roi", "region_of_interest_boundary", region_of_interest_boundary)

    return region_of_interest_boundary

# type aliases for reusability
Point2D = tuple[int, int]
LineEndpoints = tuple[Point2D, Point2D]

def get_hough_lines(
    image: NDArray[np.generic], 
    min_angle: float, max_angle: float, 
    min_separation_distance: float, 
    min_separation_angle: float
) -> Union[LineEndpoints, list[LineEndpoints]]:
    """
    Extract Hough lines from an image based on specified angle and separation constraints.

    Parameters
    ----------
    image : NDArray[np.generic]
        The input image from which to extract Hough lines
    min_angle : float
        The minimum angle boundary for line detection
    max_angle : float
        The maximum angle boundary for line detection
    min_separation_distance : float
        The minimum distance separation required between detected lines
    min_separation_angle : float
        The minimum angle separation required between detected lines

    Returns
    -------
    Union[LineEndpoints, list[LineEndpoints]]
        The endpoints of the detected line(s), represented as a single pair of 2D points 
        or a list of pairs depending on the detection results.
    """
    return get_best_hough_lines(
        image, min_angle, max_angle, min_separation_distance, min_separation_angle
    )


def get_box_lines(
    boundary: NDArray[np.generic], 
    image: Optional[NDArray[np.generic]] = None, 
    min_separation_distance: float = 5, 
    min_separation_angle: float = 5,
    angles: Optional[dict[str, float]] = None
) -> dict[str, NDArray]:
    """
    Split a boundary image into regions (left, right, top, bottom) and extract Hough lines 
    for each region using specified angle and separation constraints

    Parameters
    ----------
    boundary : NDArray[np.generic]
        The input boundary image to be split and analyzed
    image : Optional[NDArray[np.generic]], optional
        An optional base image for debugging and visualization overlays
    min_separation_distance : float, optional, default 5
        The minimum distance separation required between detected lines in Hough transform
    min_separation_angle : float, optional, default 5
        The minimum angle separation required between detected lines in Hough transform
    angles : Optional[dict[str, float]], optional
        A dictionary specifying minimum and maximum angle bounds for vertical and horizontal lines
        Expected keys are "vertical_min", "vertical_max", "horizontal_min", and "horizontal_max"
        Default uses standard preset bounds

    Returns
    -------
    dict[str, NDArray]
        A dictionary mapping region names ("left", "right", "top", "bottom") to arrays of detected Hough lines
    """
    height, width = boundary.shape
    [half_width, half_height] = np.floor([0.5 * width, 0.5 * height]).astype(int)

    if angles is None:
        angles = {
            "vertical_min": -10,
            "vertical_max": 10,
            "horizontal_min": -120,
            "horizontal_max": -70
        }
    timeStart("split image")
    image_regions = {
        "left": boundary[0:height, 0:half_width],
        "right": boundary[0:height, half_width:width],
        "top": boundary[0:half_height, 0:width],
        "bottom": boundary[half_height:height, 0:width],
    }
    timeEnd("split image")

    timeStart("get hough lines")
    hough_lines = {
        "left": np.array(
            get_hough_lines(
                image_regions["left"], 
                min_angle=angles.get("vertical_min", -10), 
                max_angle=angles.get("vertical_max", 10),
                min_separation_distance=min_separation_distance,
                min_separation_angle=min_separation_angle
            )
        ),
        "right": np.array(
            get_hough_lines(
                image_regions["right"], 
                min_angle=angles.get("vertical_min", -10), 
                max_angle=angles.get("vertical_max", 10),
                min_separation_distance=min_separation_distance,
                min_separation_angle=min_separation_angle
            )
        ),
        "top": np.array(
            get_hough_lines(
                image_regions["top"], 
                min_angle=angles.get("horizontal_min", -120), 
                max_angle=angles.get("horizontal_max", -70),
                min_separation_distance=min_separation_distance,
                min_separation_angle=min_separation_angle
            )
        ),
        "bottom": np.array(
            get_hough_lines(
                image_regions["bottom"], 
                min_angle=angles.get("horizontal_min", -120), 
                max_angle=angles.get("horizontal_max", -70),
                min_separation_distance=min_separation_distance,
                min_separation_angle=min_separation_angle 
            )
        ),
    }
    
    timeEnd("get hough lines")

    # hough_lines["bottom"] += [0, half_height]
    # hough_lines["right"] += [half_width, 0]

    # check if hough lines are valid before attempting to shift
    if hough_lines.get('bottom') is not None and len(hough_lines['bottom']) > 0:
        hough_lines['bottom'] = np.array(hough_lines['bottom']) + [0, half_height]

    if hough_lines.get('right') is not None and len(hough_lines['right']) > 0:
        hough_lines['right'] = np.array(hough_lines['right']) + [half_width, 0]

    print("found these hough lines:")
    print(hough_lines)

    if Debug.active:
        image = gray2rgb(boundary)
        line_coords = [
            skidraw.line(line[0][1], line[0][0], line[1][1], line[1][0])
            for line in hough_lines.values()
        ]
        for line in line_coords:
            rr, cc = line
            mask = (rr >= 0) & (rr < image.shape[0]) & (cc >= 0) & (cc < image.shape[1])
            image[rr[mask], cc[mask]] = [255, 0, 0]
        Debug.save_image("roi", "hough_lines", image)

    return hough_lines


def get_corners(
    lines: dict[str, NDArray], 
    image: Optional[NDArray[np.generic]] = None
)-> dict[str, Point2D]:
    """
    Calculate the corner intersections of box boundary lines, falling back to image 
    boundaries if any lines are missing, and optionally record corner metrics and debug images

    Parameters
    ----------
    lines : dict[str, NDArray]
        A dictionary mapping border names ("left", "right", "top", "bottom") to arrays of lines
    image : Optional[NDArray[np.generic]], optional
        An optional base image used for fallback dimension checks and visualization overlays

    Returns
    -------
    dict[str, Point2D]
        A dictionary mapping corner names ("top_left", "top_right", "bottom_left", "bottom_right") 
        to integer 2D coordinate tuples (x, y)
    """
    # perform check for missing boundary lines
    missing_lines = any(
        lines.get(border) is None or len(lines[border]) == 0
        for border in ["left", "right", "top", "bottom"]
    )

    timeStart("find intersections")
    if missing_lines:
        print("[WARNING] Could not detect all boundary lines. Falling back on image boundaries")
        h, w = image.shape[:2]

        # use image boundaries for fallback boundaries
        corners = {
            "top_left": np.array([0,0]),
            "top_right": np.array([w-1, 0]),
            "bottom_left": np.array([0, h-1]),
            "bottom_right": np.array([w-1, h-1]),
        }
    else:
        corners = {
            "top_left": seg_intersect(lines["top"], lines["left"]),
            "top_right": seg_intersect(lines["top"], lines["right"]),
            "bottom_left": seg_intersect(lines["bottom"], lines["left"]),
            "bottom_right": seg_intersect(lines["bottom"], lines["right"]),
        }

    # turn corners into tuples of the form (x, y), where x and y are integers
    corners = {
        corner_name: tuple(coord.astype(int)) for corner_name, coord in corners.items()
    }
    timeEnd("find intersections")

    if Debug.active:
        image_copy = np.copy(image)
        inner_circles = {
            corner_name: skidraw.circle(corner[1], corner[0], 10, shape=image.shape)
            for corner_name, corner in corners.items()
        }
        outer_circles = {
            corner_name: skidraw.circle(corner[1], corner[0], 50, shape=image.shape)
            for corner_name, corner in corners.items()
        }
        for corner_name in inner_circles:
            image_copy[outer_circles[corner_name]] = 0.0
            image_copy[inner_circles[corner_name]] = 1.0
        Debug.save_image("roi", "roi_corners", image_copy)

    if Record.active:
        from .utilities import poly_area2D
        from .quality_control import points_to_rho_theta

        corners_clockwise = [
            corners["top_left"],
            corners["top_right"],
            corners["bottom_right"],
            corners["bottom_left"],
        ]
        roi_area = poly_area2D(corners_clockwise)
        _, roi_angle_top = points_to_rho_theta(
            corners["top_left"], corners["top_right"]
        )
        _, roi_angle_bottom = points_to_rho_theta(
            corners["bottom_right"], corners["bottom_left"]
        )
        _, roi_angle_left = points_to_rho_theta(
            corners["top_left"], corners["bottom_left"]
        )
        _, roi_angle_right = points_to_rho_theta(
            corners["bottom_right"], corners["top_right"]
        )

        Record.record("roi_area", roi_area)
        Record.record("roi_angle_top", float(f"{roi_angle_top:.4f}"))
        Record.record("roi_angle_bottom", float(f"{roi_angle_bottom:.4f}"))
        Record.record("roi_angle_left", float(f"{roi_angle_left:.4f}"))
        Record.record("roi_angle_right", float(f"{roi_angle_right:.4f}"))

    return corners


def get_roi(
    image: NDArray[np.generic], 
    scale: int, 
    config: dict[str, Any] = {}
) -> dict[str, Point2D]:
    """
    Extract the region of interest (ROI) corners from an input image using boundary detection, 
    Hough line extraction, and intersection calculations governed by a configuration dictionary

    Parameters
    ----------
    image : NDArray[np.generic]
        The input grayscale or color image from which to extract the ROI corners
    scale : int
        The scaling factor applied during boundary detection and trace width calculations
    config : dict[str, Any], optional
        A configuration dictionary containing optional parameters such as:
        - "base_trace_width": int (default 17)
        - "min_separation_distance": float (default 5)
        - "min_separation_angle": float (default 5)
        - "angles": dict[str, float] (optional angle constraints dictionary)

    Returns
    -------
    dict[str, Point2D]
        A dictionary mapping the four ROI corners ("top_left", "top_right", "bottom_left", "bottom_right") 
        to integer 2D coordinate tuples (x, y)
    """
    base_trace_width = config.get('base_trace_width', 17)
    min_separation_distance = config.get('min_separation_distance', 5)
    min_separation_angle = config.get('min_separation_angle', 5)
    angles_config = config.get('angles')
    boundary = get_boundary(image, scale=scale, base_trace_width=base_trace_width)
    lines = get_box_lines(
        boundary, 
        image=image,
        min_separation_distance=min_separation_distance,
        min_separation_angle=min_separation_angle,
        angles=angles_config)
    
    corners = get_corners(lines, image=image)
    return corners


def corners_to_geojson(corners: dict[str, Point2D]) -> geojson.Feature:
    """
    Convert a dictionary of corner coordinates into a GeoJSON Feature containing a Polygon

    Parameters
    ----------
    corners : dict[str, Point2D]
        A dictionary mapping corner names ("top_left", "top_right", "bottom_right", "bottom_left") 
        to integer 2D coordinate tuples (x, y)

    Returns
    -------
    geojson.Feature
        A GeoJSON Feature object representing the polygon formed by the ROI corners
    """
    newPolygon = geojson.Polygon(
        [
            [
                corners["top_left"],
                corners["top_right"],
                corners["bottom_right"],
                corners["bottom_left"],
                corners["top_left"],
            ]
        ]
    )
    newFeature = geojson.Feature(geometry=newPolygon)
    return newFeature

# reverse helper function
def geojson_to_corners(feature: Union[geojson.Feature, dict, Any]) -> dict[str, Point2D]:
    """
    Convert a GeoJSON Feature or geometry dictionary back into a dictionary of corner coordinates

    Parameters
    ----------
    feature : Union[geojson.Feature, dict, Any]
        The GeoJSON Feature, geometry dictionary, or object containing geometry coordinates 
        representing the polygon corners.

    Returns
    -------
    dict[str, Point2D]
        A dictionary mapping corner names ("top_left", "top_right", "bottom_right", "bottom_left") 
        to 2D coordinate tuples.
    """
    if isinstance(feature, dict):
        geometry = feature.get("geometry", feature)
    else:
        geometry = getattr(feature, "geometry", feature)

    coords = geometry["coordinates"][0] if isinstance(geometry, dict) else geometry.coordinates[0]

    corners = {
        "top_left": tuple(coords[0]),
        "top_right": tuple(coords[1]),
        "bottom_right": tuple(coords[2]),
        "bottom_left": tuple(coords[3]),
    }

    return corners