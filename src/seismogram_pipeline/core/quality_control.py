import numpy as np
from .utilities import poly_area2D
from typing import Any

def check_roi(
    corners: dict[str, tuple[Any, ...]],
    target_area: int = 65352425,
    acceptable_error: float = 0.05 
) -> bool:
    """
    Checks if computed region of interest falls within an acceptable error

    Parameters
    ----------
    corners : dict[str, tuple[Any, ...]]
        Dictionary of key-defined corners of the image
    target_area : int
        Expected ideal area for the region of interest
    acceptable_error : float
        Maximum allowed fractional error

    Returns
    -------
    within_error : bool
        Whether the fractional error is within the acceptable error 
    """
    corners_clockwise = [
        corners["top_left"],
        corners["top_right"],
        corners["bottom_right"],
        corners["bottom_left"],
    ]
    roi_area = poly_area2D(corners_clockwise)
    error = abs(roi_area - target_area) / target_area

    return error <= acceptable_error


# transform coordinates describing a line
# from two (x, y) pairs to one (rho, theta) pair
# (i.e. to hough space)
def points_to_rho_theta(
    p0: tuple[float, float],
    p1: tuple[float, float]
) -> tuple[float, float]:
    """
    Converts input points into Hough space parameters: rho & theta 

    Parameters
    ----------
    p0, p1 : tuple[float, float]
        Corner points
    
    Returns
    -------
    (rho, theta) : tuple[float, float]
        Hough Space parameters of the connecting line
    """
    x0, y0 = p0
    x1, y1 = p1

    if x1 == x0:
        # vertical line
        return (x1, 0)

    if y1 == y0:
        # horizontal line
        return (y1, -np.pi / 2)

    slope = float(y1 - y0) / (x1 - x0)
    intercept = y1 - slope * x1
    theta = np.arctan2(-1, slope)
    # using arctan2 instead of arctan means
    # theta will always be on the interval [0, -PI]
    rho = intercept * np.sin(theta)
    return (rho, theta)
