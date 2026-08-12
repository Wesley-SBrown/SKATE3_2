# -*- coding: utf-8 -*-
"""
Created on Fri Feb 13 13:05:12 2015

@author: benamy
"""

from .timer import timeStart, timeEnd
from .debug import Debug

import numpy as np
from scipy.interpolate import SmoothBivariateSpline as spline2d
from scipy.ndimage import distance_transform_edt
from skimage.morphology import convex_hull_image
from numpy.ma.core import MaskedArray
from numpy.typing import NDArray
from collections.abc import Callable
from typing import Union, Optional, Sequence
from .mitchells_best_candidate import best_candidate_sample
from .utilities import local_min

generator = Debug.random


def threshold(
    img: NDArray[np.generic], 
    threshold_function: Callable[[NDArray[np.generic]], Union[int, float]], 
    num_blocks: int, 
    block_dims: Optional[Union[tuple[int,int], NDArray[np.intp]]] = None, 
    smoothing: float = 0.003,
    min_num_blocks: int = 16,
) -> NDArray[np.generic]:
    """
    Get a smoothly varying threshold from an image by applying the threshold
    function to multiple randomly positioned blocks of the image and using
    a 2-D smoothing spline to set the threshold across the image.

    Parameters
    ----------
    img : 2-D numpy array
      The grayscale image.
    threshold_function : a function
      The threshold function should take a grayscale image as an input and
      output an int or float.
    num_blocks : int
      The number of blocks within the image to which to apply the threshold
      function. A higher number will provide better coverage across the
      image but will take longer to evaluate.
    block_dims : tuple or numpy array, optional
      The dimensions of the rectangular blocks. Dimensions should be less
      than the dimensions of the image. If left unspecified, the blocks will
      be squares with area approximately equal to two times the area of the
      image, divided by num_blocks.
    smoothing : float, optional, default 0
      A parameter to adjust the smoothness of the 2-D smoothing spline. A
      higher number increases the smoothness of the output. An input of zero
      is equivalent to interpolation.
    min_num_blocks : int, optional
      The minimum number of blocks allowed.
    Returns
    -------
    th_new : 2-D numpy array
      The threshold. The array is the same shape as the original input image.
    """
    img_dims = img.shape
    if num_blocks >= min_num_blocks:
        spline_order = 3
    else:
        spline_order = int(np.sqrt(num_blocks) - 1)
    if spline_order == 0:
        return np.ones_like(img) * threshold_function(img)

    if type(img) is MaskedArray:
        mask = img.mask
    else:
        mask = np.zeros(img_dims, dtype=bool)

    candidate_coords = np.transpose(np.nonzero(~mask))

    if block_dims is None:
        block_dim = int(round(np.sqrt(2 * img.size / num_blocks)))
        block_dims = (block_dim, block_dim)

    timeStart("select block centers")
    points = best_candidate_sample(candidate_coords, num_blocks)
    timeEnd("select block centers")

    def get_threshold_for_block(
        center: Union[Sequence[int], NDArray[np.intp]]
    ) -> Union[int, float]:
        """
        Extract a block from the image centered at the given coordinates and 
        compute its threshold value using the threshold function.

        Parameters
        ----------
        center : sequence of int or numpy array
        The coordinates representing the center of the block to extract.

        Returns
        -------
        threshold_value : int or float
        The computed threshold for the specified block.
        """
        block = get_block(img, center, block_dims)
        if type(block) is MaskedArray:
            return threshold_function(block.compressed())
        else:
            return threshold_function(block)

    timeStart(f"calculate thresholds for blocks of size {block_dim}")
    thresholds = np.asarray([get_threshold_for_block(center) for center in points])
    timeEnd(f"calculate thresholds for blocks of size {block_dim}")

    timeStart("fit 2-D spline")
    # Maybe consider using lower-order spline for large images
    # (if large indices create problems for cubic functions)
    fit = spline2d(
        points[:, 0],
        points[:, 1],
        thresholds,
        bbox=[0, img_dims[0], 0, img_dims[1]],
        kx=spline_order,
        ky=spline_order,
        s=num_blocks * smoothing,
    )
    th_new = fit(x=np.arange(img_dims[0]), y=np.arange(img_dims[1]))
    th_new = fix_border(th_new, points)
    timeEnd("fit 2-D spline")
    return th_new


def debug_blocks(
    img: NDArray[np.generic], 
    points: Sequence[Union[Sequence[int], NDArray[np.intp]]], 
    block_dims: Union[tuple[int, int], NDArray[np.intp]], 
    threshold_function: Callable[[Union[NDArray[np.generic], NDArray[np.number]]], Union[int, float]], 
    marker_circle_radius: int = 20,
) -> None:
    """
    To be used for debugging. Saves images of blocks that throw errors,
    and an additional image showing how the blocks are distributed.

    Parameters
    ----------
    img : 2-D numpy array
      The grayscale image being processed.
    points : sequence of sequences or numpy arrays
      The coordinates representing the centers of the blocks to evaluate.
    block_dims : tuple or numpy array
      The dimensions of the rectangular blocks.
    threshold_function : a function
      The threshold function applied to each block.
    marker_circle_radius : int, optional, default 20
      The radius of the circles used to mark block centers in the debug image.
    """
    from .debug import Debug
    from skimage.draw import line, circle
    from skimage.color import gray2rgb

    bad_block_points = []

    for center in points:
        block = get_block(img, center, block_dims)
        try:
            if type(block) is MaskedArray:
                threshold_function(block.compressed())
            else:
                threshold_function(block)

        except Exception as e:
            print("threshold block error")
            print(e)
            bad_block_points.append(center)
            Debug.save_image("threshold", "bad_block_" + str(center), block)

    debug_image = gray2rgb(np.copy(img))

    def get_block_corners(center, size):
        half_side = size / 2
        return [
            (center[0] + half_side, center[1] + half_side),
            (center[0] + half_side, center[1] - half_side),
            (center[0] - half_side, center[1] - half_side),
            (center[0] - half_side, center[1] + half_side),
        ]

    block_corners = [
        get_block_corners(center, block_dims[0]) for center in bad_block_points
    ]
    block_line_coords = [
        [
            line(*corners[0] + corners[1]),
            line(*corners[1] + corners[2]),
            line(*corners[2] + corners[3]),
            line(*corners[3] + corners[0]),
        ]
        for corners in block_corners
    ]

    for block in block_line_coords:
        for line_coords in block:
            rr, cc = line_coords
            mask = (
                (rr >= 0)
                & (rr < debug_image.shape[0])
                & (cc >= 0)
                & (cc < debug_image.shape[1])
            )
            debug_image[rr[mask], cc[mask]] = [1.0, 0, 0]

    for center in points:
        rr, cc = circle(center[0], center[1], 20)
        debug_image[rr, cc] = [1.0, 0, 0]

    Debug.save_image("threshold", "threshold_blocks", debug_image)


# def get_block(img, center, block_dims):
#   '''
#   Returns the rectangular subarray of **img** centered at **center**, with
#   dimensions at most equal to **block_dims**.

#   Parameters
#   -----------
#   img : 2-D numpy array
#   center : tuple or numpy array
#     The coordinates of the center of the block. Should be integer-valued.
#   block_dims : tuple or numpy array
#     The dimensions of the block. If **center** is too close to the edge of
#     **img**, the returned block will have dimensions smaller than
#     **block_dims**.

#   Results
#   ---------
#   block : 2-D numpy array
#     A subarray of **img**.
#   '''
#   img_dims = img.shape
#   upper = max(0, center[0] - block_dims[0] / 2)
#   lower = min(img_dims[0], center[0] + block_dims[0] / 2 + 1)
#   left = max(0, center[1] - block_dims[1] / 2)
#   right = min(img_dims[1], center[1] + block_dims[1] / 2 + 1)
#   block = img[upper:lower, left:right]
#   return block


def get_block(
    img: NDArray[np.generic], 
    center: Union[Sequence[int], NDArray[np.intp]], 
    block_dims: Union[Sequence[int], NDArray[np.intp]]
) -> NDArray[np.generic]:
    """
    Returns the rectangular subarray of **img** centered at **center**, with
    dimensions at most equal to **block_dims**.

    Parameters
    ----------
    img : 2-D numpy array
      The input image from which to extract the block.
    center : sequence of int or numpy array
      The coordinates (row, col) representing the center of the block.
    block_dims : sequence of int or numpy array
      The dimensions (height, width) of the block.

    Returns
    -------
    block : 2-D numpy array
      The extracted subarray from the image.
    """
    img_dims = img.shape

    upper = int(max(0, center[0] - block_dims[0] / 2))
    lower = int(min(img_dims[0], center[0] + block_dims[0] / 2 + 1))
    left = int(max(0, center[1] - block_dims[1] / 2))
    right = int(min(img_dims[1], center[1] + block_dims[1] / 2 + 1))

    block = img[upper:lower, left:right]
    return block


def get_convex_hull(
    points: NDArray[np.intp], 
    img_dims: Union[Sequence[int], tuple[int, int]]
) -> NDArray[np.bool_]:
    """
    Given an array containing the coordinates of points in a 2-D array, outputs
    the convex hull of those points.

    Parameters
    ----------
    points : 2-D numpy array
      An array of point coordinates (row, col) to compute the convex hull for.
    img_dims : tuple or sequence of int
      The dimensions (height, width) of the image space.

    Returns
    -------
    hull : 2-D boolean numpy array
      A boolean image representing the convex hull enclosing the points.
    """
    img = np.zeros(img_dims, dtype=bool)
    img[points[:, 0], points[:, 1]] = True
    return convex_hull_image(img)


def fix_border(
    spline: NDArray[np.generic], 
    sample_points: NDArray[np.intp]
):
    """
    Given coordinates of points in a 2-D array, finds the convex hull defined
    by those points. Outputs an image equal to spline within the convex hull
    and, everywhere outside the hull, equal to the value of the nearest point
    inside the hull.

    Parameters
    ----------
    spline : 2-D numpy array
      The evaluated smoothing spline over the image grid.
    sample_points : 2-D numpy array
      The coordinates (row, col) of the sample points used to generate the hull.

    Returns
    -------
    fixed_spline : 2-D numpy array
      The spline array with border values extrapolated from the nearest interior points.
    """
    border = ~get_convex_hull(sample_points, spline.shape)
    ind = distance_transform_edt(border, return_distances=False, return_indices=True)
    return spline[tuple(ind)]


def get_hist_and_background_count(
    img: NDArray[np.generic], 
    max_sample_pixels: int = 256000,
) -> tuple[NDArray[np.intp], NDArray[np.floating], NDArray[np.floating]]:
    """
    Returns a histogram of all pixel values for a grayscale image. Also
    returns the expected histogram of background pixel values.

    Parameters
    ------------
    img : 2-D numpy array
      The grayscale image. Can be either floats on the interval [0,1] or
      ints on the interval [0,255].
    max_sample_pixels : int, optional, default 256000
      The maximum number of pixels to sample for the histogram computation.

    Returns
    --------
    hist, bin_edges, background_count : 1-D numpy arrays
      The histogram bin values and edges, and the expected distribution of values
      for background (i.e. non-trace) pixels.
    """
    if np.amax(img) <= 1:
        bins = np.linspace(0, 256 / 255, num=257)
        img = np.round(255 * img) / 255
    else:
        bins = np.arange(257)

    # Assume that data from 256,000 (256 * 1000) pixels is sufficient
    if img.size > max_sample_pixels:
        prob = float(256 * 1000) / img.size
        img = img[(generator.random_sample(size=img.shape) < prob)]
    hist_counts, bin_edges = np.histogram(img, bins=bins)

    # Pad counts with 1 (to eliminate zeros)
    hist_counts = hist_counts + 1

    expected_background_counts = get_expected_background_pixel_counts(hist_counts)

    return hist_counts, bin_edges, expected_background_counts


def get_expected_background_pixel_counts(
    pixel_counts: NDArray[np.number]
) -> NDArray[np.floating]:
    """
    Computes the expected distribution of background pixel values assuming 
    symmetry around the peak background pixel color.

    Parameters
    ----------
    pixel_counts : 1-D numpy array
      The histogram counts of pixel values.

    Returns
    -------
    expected_background_counts : 1-D numpy array
      The expected counts for background pixels across the color bins.
    """
    peak_pixel_color = get_most_common_background_pixel_color(pixel_counts)

    # Copy the histogram values from [0 -> peak] into expected_background_counts
    expected_background_counts = np.zeros((256))
    expected_background_counts[0 : (peak_pixel_color + 1)] = pixel_counts[
        0 : (peak_pixel_color + 1)
    ]

    # Reflect the histogram values from [0 -> peak) and copy them
    # into expected_background_counts[peak+1 -> 2*peak+1]; this assumes the distribution
    # of background pixel values is symmetrical about its peak
    if peak_pixel_color != 0:
        expected_background_counts[
            (peak_pixel_color + 1) : (2 * peak_pixel_color + 1)
        ] = pixel_counts[(peak_pixel_color - 1) :: -1]

    return expected_background_counts


def get_most_common_background_pixel_color(
    pixel_counts: NDArray[np.number], 
    max_background_intensity_peak: int = 128
) -> int:
    """
    Finds the most common background pixel color by locating the peak 
    within the allowed maximum background intensity range.

    Parameters
    ----------
    pixel_counts : 1-D numpy array
      The histogram counts of pixel values.
    max_background_intensity_peak : int, optional, default 128
      The upper bound of intensity values to search for the background peak.

    Returns
    -------
    peak_color : int
      The pixel intensity value corresponding to the peak of the background distribution.
    """
    # Assume the most common pixel value < 128 is the peak
    # of the background pixel distribution
    return np.argmax(pixel_counts[0:max_background_intensity_peak])


def make_background_thresh_fun(prob_background: float = 1):

    def get_background_thresh(img: NDArray[np.generic])-> Union[float, int]:
        """
        Identifies a threshold for pixel intensity below which pixels are part of
        the background with at least a **prob_background** estimated probability.
        This works by assuming that most of the image is dark background, the
        single most common pixel brightness is the average brightness for a
        background pixel, and that the brightnesses of background pixels are
        distributed like the normal distribution.

        Parameters
        ------------
        img : 2-D numpy array
          The grayscale image. Can be either floats on the interval [0,1] or
          ints on the interval [0,255].
        prob_background : float, optional
          The minimum (estimated) probability that a pixel is part of the
          background. Must be <=1. Lower numbers will likely result in a higher
          returned threshold.

        Returns
        --------
        th : float or int
          The threshold below which pixels in the image are likely part of the
          background.
        """
        hist, bin_edges, background_count = get_hist_and_background_count(img)
        probabilities = np.minimum(background_count / hist, 0.99)
        peak_pixel_color = get_most_common_background_pixel_color(hist)
        probabilities[0 : (peak_pixel_color + 1)] = 1
        th = bin_edges[np.argmin(probabilities >= prob_background) - 1]
        return th

    return get_background_thresh


def make_foreground_thresh_fun(prob_foreground: float = 0.99):

    def get_foreground_thresh(img: NDArray[np.generic])-> Union[float, int]:
        """
        Identifies a threshold for pixel intensity above which pixels are part of
        the foreground with at least a **prob_background** estimated probability.
        This works by assuming that most of the image is dark background, the
        single most common pixel brightness is the average brightness for a
        background pixel, and that the brightnesses of background pixels are
        distributed like the normal distribution.

        Parameters
        ------------
        img : 2-D numpy array
          The grayscale image. Can be either floats on the interval [0,1] or
          ints on the interval [0,255].
        prob_foreground : float, optional
          The minimum (estimated) probability that a pixel is part of the
          background. Must be < 1. Lower numbers will likely result in a lower
          returned threshold.

        Returns
        --------
        th : float or int
          The threshold above which pixels in the image are likely part of the
          foreground.
        """
        hist, bin_edges, background_count = get_hist_and_background_count(img)
        probabilities = 1 - np.minimum(background_count / hist, 1)
        th = bin_edges[np.argmax(probabilities >= prob_foreground)]
        return th

    return get_foreground_thresh


def background_threshold(
    img: NDArray[np.generic], 
    prob_background: float = 1.0, 
    num_blocks: Optional[int] = None, 
    block_dims: Union[Sequence[int], NDArray[np.intp]] = None,
    smoothing_factor: float = 0.003, 
    default_block_pixel_area: int = 250000
) -> NDArray[np.generic]:
    """
    The pixel intensity at every location in the image below which the pixel
    is likely part of the dark background. The threshold varies smoothly
    across the image.

    Parameters
    ------------
    img : 2-D numpy array
      The grayscale image. Can be either floats on the interval [0,1] or
      ints on the interval [0,255].
    prob_background : float, optional, default 1.0
      The minimum probability (estimated) that a pixel below the threshold
      is part of the backround. Must be <= 1. Lower numbers will result in
      higher thresholds.
    num_blocks : int, optional
      The number of blocks of the image to use to create the threshold.
    block_dims : tuple or numpy array
      The dimensions of the rectangular blocks. Dimensions should be less
      than the dimensions of the image. If left unspecified, the blocks will
      be squares with area approximately equal to two times the area of the
      image, divided by num_blocks.
    smoothing_factor : float, optional, default 0.003
      A parameter to adjust the smoothness of the 2-D smoothing spline.
    default_block_pixel_area : int, optional, default 250000
      The default area in pixels used to estimate num_blocks when not provided.

    Returns
    ----------
    th : 2-D numpy array
      The varying threshold that separates the dark background from the rest
      of the image. Has the same size and dimensions as img.
    """
    # Default number of blocks assumes 500x500 blocks are a good size
    if num_blocks is None:
        num_blocks = int(np.ceil(2 * img.size / default_block_pixel_area))

    get_background_thresh = make_background_thresh_fun(prob_background)

    return threshold(
        img, get_background_thresh, num_blocks, block_dims, smoothing=smoothing_factor
    )


def foreground_threshold(
    img: NDArray[np.generic], 
    prob_foreground: float = 0.99, 
    num_blocks: Optional[int] = None, 
    block_dims: Union[Sequence[int], NDArray[np.intp]] = None,
    smoothing_factor: float = 0.003, 
    default_block_pixel_area: int = 250000
) -> NDArray[np.generic]:
    """
    The pixel intensity at every location in the image above which the pixel
    is likely part of the bright foreground. The threshold varies smoothly
    across the image.

    Parameters
    ----------
    img : 2-D numpy array
      The grayscale image. Can be either floats on the interval [0,1] or
      ints on the interval [0,255].
    prob_foreground : float, optional, default 0.99
      The minimum probability (estimated) that a pixel above the threshold
      is part of the foreground. Must be <= 1. Lower numbers will result in
      lower thresholds.
    num_blocks : int, optional
      The number of blocks of the image to use to create the threshold.
    block_dims : tuple or numpy array
      The dimensions of the rectangular blocks. Dimensions should be less
      than the dimensions of the image. If left unspecified, the blocks will
      be squares with area approximately equal to two times the area of the
      image, divided by num_blocks.
    smoothing_factor : float, optional, default 0.003
      A parameter to adjust the smoothness of the 2-D smoothing spline.
    default_block_pixel_area : int, optional, default 250000
      The default area in pixels used to estimate num_blocks when not provided.

    Returns
    -------
    th : 2-D numpy array
      The varying threshold that separates the bright foreground from the
      rest of the image. Has the same size and dimensions as img.
    """
    # Default number of blocks assumes 500x500 blocks are a good size
    if num_blocks is None:
        num_blocks = int(np.ceil(2 * img.size / default_block_pixel_area))

    get_foreground_thresh = make_foreground_thresh_fun(prob_foreground)

    return threshold(
        img, get_foreground_thresh, num_blocks, block_dims, smoothing=smoothing_factor
    )


def flatten_background(
    img: NDArray[np.generic],
    prob_background: float = 1.0,
    num_blocks: Optional[int] = None,
    block_dims: Optional[Union[Sequence[int], NDArray[np.integer]]] = None,
    return_background: bool = False,
    img_gray: Optional[NDArray[np.generic]] = None,
    smoothing_factor: float = 0.003, 
    default_block_pixel_area: int = 250000,
) -> Union[NDArray[np.generic], tuple[NDArray[np.generic], NDArray[np.bool_]]]:
    """
    Finds the pixel intensity at every location in the image below which the
    pixel is likely part of the dark background. Pixels darker than this
    threshold are replaced by the value of the threshold at its location. This
    eliminates unusually dark regions.

    Parameters
    ------------
    img : 2-D numpy array
      The grayscale image. Can be either floats on the interval [0,1] or
      ints on the interval [0,255].
    prob_background : float, optional
      The minimum probability (estimated) that a pixel below the threshold
      is part of the backround. Must be <= 1. Lower numbers will result in
      higher thresholds.
    num_blocks : int, optional
      The number of blocks of the image to use to create the threshold.
    block_dims : tuple or numpy array
      The dimensions of the rectangular blocks. Dimensions should be less
      than the dimensions of the image. If left unspecified, the blocks will
      be squares with area approximately equal to two times the area of the
      image, divided by num_blocks.
    return_background : bool, optional
      If True, returns a tuple containing both the flattened image and the 
      boolean background mask.
    img_gray : 2-D numpy array, optional
      Optional reference grayscale image used for local minima calculation.
    smoothing_factor : float, optional
      Smoothing parameter for the 2-D smoothing spline threshold.
    default_block_pixel_area : int, optional
      The default area in pixels used to estimate num_blocks when not provided.
    
    Returns
    --------
    flattened : 2-D numpy array
      An image equal to the input grayscale image where pixels are above
      the brightness of the background threshold and equal to the threshold
      everywhere else.
    background : 2-D numpy array of bools
      The pixels below the background threshold.
    """
    # Default number of blocks assumes 500x500 blocks are a good size
    if num_blocks is None:
        num_blocks = int(np.ceil(2 * img.size / default_block_pixel_area))

    timeStart(f"calculate background threshold with {num_blocks} blocks")
    get_background_thresh = make_background_thresh_fun(prob_background)
    background_level = threshold(
        img, get_background_thresh, num_blocks, block_dims, smoothing=smoothing_factor
    )
    timeEnd(f"calculate background threshold with {num_blocks} blocks")

    timeStart("select dark pixels")
    dark_pixels = img < background_level
    timeEnd("select dark pixels")

    timeStart("raise dark pixels")
    flattened = np.where(dark_pixels, background_level, img)
    timeEnd("raise dark pixels")

    local_min_gray = local_min(img_gray)
    Debug.save_image("threshold", "local_min_gray", local_min_gray)

    timeStart("union dark pixels, minima, and mask regions")
    background = dark_pixels | local_min_gray | img.mask
    timeEnd("union dark pixels, minima, and mask regions")
    Debug.save_image("threshold", "background", background)

    """
  background_with_mask barely differs from background, but it
  somehow differs enough to cause the pipeline to find different
  numbers of intersections and segments. The differences seem to be
  at the boundary of the mask, so I suspect they only result in
  segments that will end up being deleted anyway.

  TODO: Come back and check this after adding automated deletion
  of segments that pass outside the ROI (assuming this isn't
  already a thing).

  bennlich 9/21

  """
    # local_min_mask = local_min(img)
    # Debug.save_image("threshold", "local_min_mask", local_min_mask)

    # timeStart("union dark pixels, minima, and mask regions")
    # background_with_mask = dark_pixels | local_min_mask | img.mask
    # timeEnd("union dark pixels, minima, and mask regions")
    # Debug.save_image("threshold", "background_with_mask", background_with_mask)

    if return_background is False:
        return flattened
    else:
        return (flattened, background)
