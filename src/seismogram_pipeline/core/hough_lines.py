from typing import Union
import numpy as np
import numpy.typing as npt
import os, yaml
from skimage.transform import hough_line, hough_line_peaks

from .debug import Debug
from .utilities import normalize
from .stats_recorder import Record

# type aliases for reusability
Point2D = tuple[int, int]
LineEndpoints = tuple[Point2D, Point2D]

def get_best_hough_lines(
    image: npt.NDArray[np.generic],
    min_angle: float, 
    max_angle: float, 
    min_separation_distance: Union[int, float], 
    min_separation_angle: Union[int, float], 
    angular_step: float = 0.5,
    num_peaks: int = 150,
    threshold_factor: float = 0.2
) -> Union[LineEndpoints, list[LineEndpoints]]:
    """
    Detects Hough Lines and returns the best matching line endpoints

    Parameters
    ----------
    image : NumPy array of numbers
        A 2-D binary or grayscale input image array
    min_angle : float
        Minimum search angle (degrees)
    max_angle : float
        Maximum search angle (degrees)
    min_separation_distance : int or float
        Minimum distance (pixels) separating detected peaks in the accumulator
    min_separation_angle : int or float
        Minimum angle (degrees) separating detected peaks in the accumulator
    angular_step : float, default 0.5
        Angular step size (degrees) for generating search angles
    num_peaks : int, default 150
        Maximum number of peaks to consider from the Hough accumulator
    threshold_factor : float, default 0.2
        Fraction of the maximum accumulator value
        Used as minimum peak threshold
    
    Returns
    -------
    line : LineEndpoints or list[LineEndpoints]
        Endpoints `((x0, y0), (x1, y1))` of the strongest line peak
        Empty list if no peaks detected
    """
    angles = np.deg2rad(np.arange(min_angle, max_angle, angular_step))
    hough, angles, distances = hough_line(image, angles)

    peak_hough, peak_angles, peak_distances = hough_line_peaks(
        hough,
        angles,
        distances,
        num_peaks=num_peaks,
        threshold=threshold_factor * np.amax(hough),
        min_distance=min_separation_distance,
        min_angle=min_separation_angle
    )

    if len(peak_hough) == 0:
        return []
    
    best_hough_idx = np.argmax(peak_hough)
    line = get_line_endpoints_in_image(
        image, peak_angles[best_hough_idx], peak_distances[best_hough_idx]
    )
    return line


def get_all_hough_lines(
    image: npt.NDArray[np.generic], 
    min_angle: float,
    max_angle: float, 
    min_separation_distance: Union[int, float], 
    min_separation_angle: Union[int, float], 
    angular_step: float = 0.5,
    num_peaks: int = 150,
    threshold_factor: float = 0.2
)-> list[LineEndpoints]:
    """
    Detects Hough Lines and returns endpoints for all peaks found

    Parameters
    ----------
    image : NumPy array of numbers
        2-D binary or grayscale image array
    min_angle : float
        Minimum search angle (degrees)
    max_angle : float
        Maximum search angle (degrees)
    min_separation_distance : int or float
        Minimum distance (pixels) separating detected peaks in the accumulator
    min_separation_angle : int or float
        Minimum angle (degrees) separating detected peaks in the accurmulator
    angular_step : float, default 0.5
        Angular step size (degrees) for generating search angles
    num_peaks : int, default 150
        Maximum number of peaks to consider from the Hough accumulator
    threshold_factor : float, default 0.2
        Fraction of the maximum accumulator value
        Used as minimum peak threshold
    
    Returns
    -------
    lines : list[LineEndpoints]
        A list of coordinate tuples `[((x0, y0), (x1, y1)), ...]` representing 
        all detected line endpoints.
    
    """

    # coerce floats to ints - SciPy requirement
    min_separation_distance = int(round(min_separation_distance))
    min_separation_angle = int(round(min_separation_angle))

    angles = np.deg2rad(np.arange(min_angle, max_angle, angular_step))
    hough, angles, distances = hough_line(image, angles)

    Debug.save_image("hough", "accumulator", normalize(hough))

    _, peak_angles, peak_distances = hough_line_peaks(
        hough,
        angles,
        distances,
        num_peaks=num_peaks,
        threshold=threshold_factor * np.amax(hough),
        min_distance=min_separation_distance,
        min_angle=min_separation_angle,
    )

    lines = [
        get_line_endpoints_in_image(image, angle, radius)
        for angle, radius in zip(peak_angles, peak_distances)
    ]

    if Debug.active:
        peak_angle_idxs = [np.where(angles == angle)[0][0] for angle in peak_angles]
        peak_rho_idxs = [
            np.where(distances == distance)[0][0] for distance in peak_distances
        ]
        peak_coords = list(zip(peak_rho_idxs, peak_angle_idxs))
        peaks = np.zeros(hough.shape)
        for coord in peak_coords:
            peaks[coord] = 1
        Debug.save_image("hough", "accumulator_peaks", peaks)

    if Record.active:
        # Thought get_max_theta_idx might be a useful way to filter
        # real meanlines from spurious meanlines, but it's not
        # reliable when the image is saturated with incorrect
        # meanlines. Filtering lines based on the ROI angle
        # was more effective.

        # max_theta_idx = get_max_theta_idx(hough)
        # Record.record("theta_mode", angles[max_theta_idx])

        # in radians
        average_meanline_angle = np.mean(peak_angles)
        std_deviation_meanline_angle = np.std(peak_angles)

        Record.record("average_meanline_angle", float(f"{average_meanline_angle:.4f}"))
        Record.record(
            "std_deviation_meanline_angle", float(f"{std_deviation_meanline_angle:.4f}")
        )

    return lines


def bin_hough(
    hough: npt.NDArray[np.generic],
    rho_bin_size: int
) -> npt.NDArray[np.generic]:
    """
    Bins the hough accumulator matrix along the rho axis

    Parameters
    ----------
    hough : NumPy array of numbers
        2-D Hough transform accumulator array (rho x theta)
    rho_bin_size : int
        Number of consecutive rho bins to aggregate

    Returns
    -------
    binned_hough : NumPy array of numbers
        2-D array representing the downsampled accumulator matrix along rho axis
    """
    binned_hough = np.zeros([int(hough.shape[0] / rho_bin_size), hough.shape[1]])
    for rho in range(0, binned_hough.shape[0]):
        slice_start = rho * rho_bin_size
        slice_end = slice_start + rho_bin_size
        binned_hough[rho, :] = np.sum(hough[slice_start:slice_end, :], axis=0)
    return binned_hough


def get_max_theta_idx(
    hough: npt.NDArray[np.generic], 
    threshold_factor: float = 0.2
) -> int:
    """
    Returns the column (theta) of the hough transform with the
    most above-threshold bins.

    Parameters
    ----------
    hough : NumPy array of numbers
        2-D Hough transform accumulator array (rho x theta)
    threshold_factor : float
        Fraction of the maximum accumulator value
        Used as a threshold cutoff
    
    Returns
    -------
    max_theta_idx : int
        Angle column index corresponding to the peak count of threshold bins

    """
    thresh_hough = threshold_hough(hough, threshold_factor * np.amax(hough))
    Debug.save_image("hough", "thresholded_accumulator", normalize(thresh_hough))
    # find the column with the most above-threshold bins
    sum_thresh_hough = np.sum(thresh_hough, axis=0)
    max_theta_idx = np.argmax(sum_thresh_hough)
    return max_theta_idx


def threshold_hough(
    hough: npt.NDArray[np.generic], 
    threshold: float
) -> npt.NDArray[np.generic]:
    """
    Applies a binary threshold mask to a Hough transform accumulator matrix

    Parameters
    ----------
    hough : NumPy array of numbers
        2-D Hough transform accumulator array (rho x theta)
    threshold : float
        Cutoff intensity value. Bins below this threshold are set to 0
        Bins at or above are set to 1

    Returns
    -------
    thresh_hough : NumPy array of numbers
        A binary 2-D array representing the thresholded accumulator matrix
    """
    thresh_hough = np.copy(hough)
    thresh_hough[hough < threshold] = 0
    thresh_hough[hough >= threshold] = 1
    return thresh_hough


"""
Tried doing some fancier stuff with the hough accumulator matrix here, but it didn't work out.

"""
# from scipy.ndimage.filters import gaussian_filter1d
# from scipy.signal import argrelextrema

# def get_hough_meanlines(image, min_angle, max_angle, min_separation_distance, min_separation_angle):
#   angles = np.deg2rad(np.arange(min_angle, max_angle, 0.5))
#   hough, angles, distances = hough_line(image, angles)

#   rho_bin_size = min_separation_distance
#   binned_hough = np.zeros([int(hough.shape[0]/rho_bin_size), hough.shape[1]])

#   def bin_idx_to_idx(bin_idx):
#     return int(bin_idx*rho_bin_size + rho_bin_size/2)

#   def bin_idx_to_rho(bin_idx):
#     return distances[bin_idx_to_idx(bin_idx)]

#   for rho in range(0, binned_hough.shape[0]):
#     slice_start = rho*rho_bin_size
#     slice_end = slice_start+rho_bin_size
#     binned_hough[rho, :] = np.sum(hough[slice_start:slice_end, :], axis=0)

#   Debug.save_image("hough", "accumulator", normalize(hough))
#   Debug.save_image("hough", "binned_accumulator", normalize(binned_hough))

#   # threshold the accumulator
#   thresh_binned_hough = np.copy(binned_hough)
#   binned_threshold = 0.3*np.amax(binned_hough)
#   thresh_binned_hough[binned_hough < binned_threshold] = 0
#   thresh_binned_hough[binned_hough >= binned_threshold] = 1

#   # find the column with the most above-threshold bins
#   sum_thresh_binned_hough = np.sum(thresh_binned_hough, axis=0)
#   theta_max_idx = np.argmax(sum_thresh_binned_hough)

#   extrema = argrelextrema(binned_hough[:, theta_max_idx], np.greater)
#   print(f"extrema: {extrema[0]}") 
#   print(f"num extrema: {len(extrema[0])}")

#   peak_angles = angles[theta_max_idx] * np.ones(len(extrema[0]))
#   peak_distances = [bin_idx_to_rho(bin_idx) for bin_idx in extrema[0]]
#   # peak_distances = [distances[bin_idx] for bin_idx in extrema[0]]

#   return [ get_line_endpoints_in_image(image, angle, radius) for angle, radius in zip(peak_angles, peak_distances)]


def get_line_endpoints_in_image(
    image: npt.NDArray[np.generic], 
    angle: float, 
    radius: float
) -> LineEndpoints:
    """
    Calculates the boundary endpoint coordinates of a line in the image frame

    Uses polar parametrization to determine where a detected line intersects the
    boundary of an image

    Parameters
    ----------
    image : NumPy array of numbers
        A 2-D reference image array used to derive boundary bounds (rows x columns).
    angle : float
        Line angle (radians).
    radius : float
        Distance from origin $(r)$ in pixels.

    Returns
    -------
    endpoints : LineEndpoints
        A tuple of integer coordinate pairs `((x0, y0), (x1, y1))` bounding the line.
    """
    rows, cols = image.shape
    cos_t = np.cos(angle)
    sin_t = np.sin(angle)

    points = []

    # test the four image boundaries to determine where the polar line intersects
    # previous implementation relied on strict assumption:
    #   - every non vertical line spans the entire width of the image
    # Issue: if line was steep enough, the endpoints may not reach the horizontal edges
    # within the image frame

    # from r = y * sin(theta) + x cos(theta)
    # check intersections with the left boundary (x=0)
    # check if close to 0 (floating point precision issues)
    if abs(sin_t) > 1e-7:
        y = radius / sin_t

        # check if y falls within valid range
        if 0 <= y <= rows - 1:
            points.append((0.0, y))

    # check intersection with right boundary (x=cols-1)
    if abs(sin_t) > 1e-7:
        y = (radius - (cols - 1) * cos_t) / sin_t

        if 0<= y <= rows - 1:
            points.append((float(cols - 1), y))

    # check intersection with top boundary (y=0) - flipped Cartesian
    if abs(cos_t) > 1e-7:
        x = radius / cos_t

        if 0<= x <= cols -1:
            points.append((x, 0.0))

    # check intersection with bottom boundary (y=rows-1)
    if abs(cos_t) > 1e-7:
        x = (radius - (rows - 1) * sin_t) / cos_t

        if 0<= x <= cols - 1:
            points.append((x, float(rows - 1)))

    # if the line passes through a corner - potential to have 2 boundary conditions
    # handle duplicate points
    unique_points = []
    for point in points:
        if not any(
            np.isclose(point[0], up[0], atol=1e-3) 
            and np.isclose(point[1], up[1], atol=1e-3)
            for up in unique_points
        ):
            unique_points.append(point)

    # in case 2 points weren't found, fall back
    if len(unique_points) < 2:
        return ((0,0), (cols - 1, rows - 1))

    # return the first two intersection points as ints
    point_1, point_2 = unique_points[:2]

    return (
        (int(round(point_1[0])), int(round(point_1[1]))),
        (int(round(point_2[0])), int(round(point_2[1])))
    )