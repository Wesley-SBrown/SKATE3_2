import numpy as np
import matplotlib.pyplot as plt
from skimage import color
from numpy.typing import NDArray
from typing import Optional

def gray2prism(gray: NDArray[np.generic]) -> NDArray[np.float64]:
    """
    Convert a single-channel grayscale image into an RGB image using the 'prism' colormap, 
    stripping the alpha channel

    Parameters
    ----------
    gray : NDArray[np.generic]
        The input grayscale image or 2D array to be color-mapped

    Returns
    -------
    NDArray[np.float64]
        The resulting RGB image represented as a floating-point NumPy array
    """
    cmap = plt.get_cmap("prism")
    # convert to prism colors and remove alpha channel
    rgb_img = cmap(gray)[:, :, :-1]
    return rgb_img


def image_overlay(
    img: NDArray[np.generic], 
    overlay: NDArray[np.generic], 
    mask: Optional[NDArray[np.generic]] = None
) -> NDArray:
    """
    Overlay an image or color map on top of a base image, blending them with an optional mask

    Parameters
    ----------
    img : NDArray[np.generic]
        The base image (grayscale or RGB) to be overlaid upon
    overlay : NDArray[np.generic]
        The overlay image (grayscale or RGB) to be blended onto the base image
    mask : Optional[NDArray[np.generic]], optional
        An optional mask array where True/non-zero regions retain the original base image 
        instead of the blended overlay

    Returns
    -------
    NDArray
        The combined and blended image array
    """
    if img.ndim == 2:
        img = color.gray2rgb(img)
    if overlay.ndim == 2:
        overlay = color.gray2rgb(overlay)
    if mask.ndim == 2:
        mask = np.dstack((mask, mask, mask))
    images_combined = 0.5 * (img + overlay)
    return np.where(mask, img, images_combined)
