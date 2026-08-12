# -*- coding: utf-8 -*-
"""
Created on Tue Feb 17 11:54:50 2015

@author: benamy
"""

from .timer import timeStart, timeEnd

import numpy as np
from numpy.typing import NDArray
from typing import Union

from skimage.draw import disk
from scipy.stats import percentileofscore
from skimage.morphology import dilation, erosion

# from threshold import make_background_thresh_fun


def encode_labeled_image_as_rgb(
    labeled_image: NDArray[np.intp]
) -> NDArray[np.floating]:
    """
    Encodes a 2-D integer-labeled image into a 3-D RGB image by mapping 
    the integer values across the red, green, and blue color channels.

    Parameters
    ----------
    labeled_image : 2D numpy array of ints

    Returns
    -------
    A 3D numpy array with the values of labeled_image encoded
    into red, green, and blue channels.
    """

    b = labeled_image % 256
    g = (labeled_image / 256) % 256
    r = labeled_image / 256 / 256
    return np.dstack((r, g, b))


def decode_rgb_to_labeled_image(
    rgb_image: NDArray[np.generic]
) -> NDArray[np.integer]:
    """
    Inverse of encode_labeled_image_as_rgb. Decodes a 3-D RGB image back 
    into a 2-D integer-labeled image.

    Parameters
    ----------
    rgb_image : 3-D numpy array
      The RGB image containing encoded integer labels across its channels.

    Returns
    -------
    labeled_image : 2-D numpy array of ints
      The reconstructed integer-labeled image.
    """
    r = rgb_image[:, :, 0]
    g = rgb_image[:, :, 1]
    b = rgb_image[:, :, 2]
    return r * 256 * 256 + g * 256 + b


def local_min(
    image: NDArray[np.generic], 
    min_distance: int = 2
) -> NDArray[np.bool_]:
    """
    Finds local minimums in an image using morphological erosion.

    Parameters
    ----------
    image : 2-D numpy array
      The grayscale input image. Can be either floats on the interval [0,1] or
      ints on the interval [0,255].
    min_distance : int, optional, default 2
      The minimum distance between local minima, determining the neighborhood 
      size for the structural element.

    Returns
    -------
    local_minima_mask : 2-D boolean numpy array
      A boolean mask where True indicates the presence of a local minimum.
    """
    if np.amax(image) <= 1:
        image = np.uint8(image * 255)

    selem = np.ones((2 * min_distance + 1, 2 * min_distance + 1))

    timeStart("morphological erosion")
    img = erosion(image, selem)
    timeEnd("morphological erosion")

    return image == img


def local_max(
    image: NDArray[np.generic], 
    min_distance: int = 2
) -> NDArray[np.bool_]:
    """
    Finds local maxima in an image

    Parameters
    ----------
    image : 2D numpy array
        The grayscale input image. Can be either floats on the interval [0,1] or
        ints on the interval [0,255].
    min_distance : int, optional, default 2
        The minimum distance between local minima, determining the neighborhood 
        size for the structural element.

    Returns
    -------
    local_maxima_mask : 2-D boolean mask
        Boolean mask where True indicates the presence of a local maxima
    """
    if np.amax(image) <= 1:
        image = np.uint8(image * 255)
    selem = np.ones((2 * min_distance + 1, 2 * min_distance + 1))
    img = dilation(image, selem)
    return image == img


def normalize(a: NDArray[np.number]) -> NDArray[np.number]:
    """
    Given an array, this function subtracts the minimum of the array from all
    elements and then divides all elements by the resulting maximum. All
    elements in the returned array are in the interval [0,1].

    Parameters
    ----------
    a : NDArray[np.number]
        Input array
    
    Returns
    -------
    b : NDArray[np.number]
        Normalize output array
    """
    b = (a - np.amin(a)).astype(float)
    b /= np.amax(b)
    return b


def percent_background(a: NDArray[np.number]) -> float:
    """
    Calculates the estimated percentage of background pixels in an image based 
    on the image histogram peak.

    Parameters
    ----------
    a : NDArray[np.number]
        Input image array.

    Returns
    -------
    float
        The estimated proportion of background pixels.
    """
    if np.amax(a) <= 1:
        bins = np.linspace(0, 1, num=257)
        a = np.round(255 * a) / 255
    else:
        bins = np.arange(257)
    hist, bin_edges = np.histogram(a, bins=bins)
    i = np.argmax(hist)
    num_background = 2 * np.sum(hist[0:i]) + hist[i]
    return num_background / a.size


def noise_boundaries(
    a: NDArray[np.number], 
    perc_back: float
) -> NDArray[np.floating]:
    """
    Assumes that noise from background pixels is centered around 0.
    Calculates dispersion-based noise boundaries for an image array.

    Parameters
    ----------
    a : NDArray[np.number]
        Input image array.
    perc_back : float
        Percentage or proportion of background pixels.

    Returns
    -------
    NDArray[np.floating]
        An array containing the lower and upper noise boundaries.
    """
    noise_center = percentileofscore(a.flat, 0, kind="mean")
    noise_edges = [noise_center - 25 * perc_back, noise_center + 25 * perc_back]
    dispersion = np.percentile(a.flat, noise_edges)
    noise_boundaries = 4 * np.asarray(dispersion)
    return noise_boundaries


# def gray_to_photon_count(image_gray, B_max = 1.01, B_min = 0):
#   if B_min == 0:
#     B_min = make_background_thresh_fun()(image_gray)
#   image_gray = np.maximum(image_gray, B_min)
#   image_photons = np.log(B_max - B_min) - np.log(B_max - image_gray)
#   image_photons = normalize(image_photons)
#   return image_photons


def mark_coords(
    shape: tuple[int, int], 
    coords: NDArray[np.integer]
) -> NDArray[np.bool_]:
    """
    Creates a boolean marker array of a given shape with True values at specified 
    coordinate locations.

    Parameters
    ----------
    shape : tuple of int
        Shape of the output marker array (height, width).
    coords : NDArray[np.integer]
        Array of coordinates where each row represents (row, col).

    Returns
    -------
    NDArray[np.bool_]
        Boolean array with True at the specified coordinate positions.
    """
    markers = np.zeros(shape, dtype=bool)
    for x in coords:
        markers[x[0], x[1]] = True
    return markers


def draw_circle(
    image: NDArray[np.generic], 
    coords: Union[tuple[int, int], NDArray[np.integer]], 
    radius: int
) -> None:
    """
    Draws a filled circle onto an existing image in-place at the specified coordinates.

    Parameters
    ----------
    image : NDArray[np.generic]
        Target image array to draw upon.
    coords : tuple of int or NDArray[np.integer]
        Center coordinates (row, column) of the circle.
    radius : int
        Radius of the disk/circle.
    """
    rr, cc = disk(coords[0], coords[1], radius)
    image[rr, cc] = True


"""
Linear regression functions
"""


def linear_fit(coords: NDArray[np.number]) -> NDArray[np.floating]:
    """
    Performs a 1D linear least squares fit (y = w1*x + w0) on a set of coordinates.

    Parameters
    ----------
    coords : NDArray[np.number]
        Array of coordinates where column 0 is y and column 1 is x.

    Returns
    -------
    NDArray[np.floating]
        Array of fitted weights/coefficients.
    """
    y = coords[:, 0]
    x0 = np.ones_like(coords[:, 1])
    x1 = coords[:, 1]
    A = np.array([x1, x0])
    w = np.linalg.lstsq(A.T, y)[0]
    return w


def quadratic_fit(coords: NDArray[np.number]) -> NDArray[np.floating]:
    """
    Performs a 2D quadratic least squares fit (y = w2*x^2 + w1*x + w0) on coordinates.

    Parameters
    ----------
    coords : NDArray[np.number]
        Array of coordinates where column 0 is y and column 1 is x.

    Returns
    -------
    NDArray[np.floating]
        Array of fitted weights/coefficients.
    """
    y = coords[:, 0]
    x0 = np.ones_like(coords[:, 1])
    x1 = coords[:, 1]
    x2 = coords[:, 1] ^ 2
    A = np.array([x2, x1, x0])
    w = np.linalg.lstsq(A.T, y)[0]
    return w


# from http://code.activestate.com/recipes/578275-2d-polygon-area/
# probably only works when poly is a list of vertices
# in clock-wise order
def poly_area2D(poly: list[tuple[float, float]] | NDArray[np.number]) -> float:
    """
    Calculates the area of a 2D polygon given its vertices using the Shoelace formula.
    Works when the polygon vertices are ordered sequentially (e.g., clockwise).

    Parameters
    ----------
    poly : list of tuples or NDArray[np.number]
        Sequence of (x, y) or (row, col) coordinates representing the polygon vertices.

    Returns
    -------
    float
        The calculated absolute area of the polygon.
    """
    total = 0.0
    N = len(poly)
    for i in range(N):
        v1 = poly[i]
        v2 = poly[(i + 1) % N]
        total += v1[0] * v2[1] - v1[1] * v2[0]
    return abs(total / 2)
