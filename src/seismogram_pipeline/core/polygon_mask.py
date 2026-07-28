from skimage.draw import polygon
import numpy as np
import numpy.typing as npt
import numpy.ma as ma
from typing import Union, Any

def get_polygon_coordinates(
    polygon_feature: npt.NDArray[np.generic]
) -> tuple[npt.NDArray[np.generic], npt.NDArray[np.generic]]:
    """
    Extract and split the y (row) and x (col) coords
    from the polygon feature array

    Parameters
    ----------
    polygon_feature : NumPy array
        Array of polygon coordinates. First col = x, second col = y
    
    Returns
    -------
    (y, x) : tuple
        Tuple of the y and x coordinate arrays    
    """
    y = polygon_feature[:, 1]
    x = polygon_feature[:, 0]
    return (y, x)


def mask_image(
    image: npt.NDArray[np.intp], 
    polygon_feature: Union[list, npt.NDArray[Any]] 
) -> ma.MaskedArray:
    """
    Create a masked array from an input image using a polygon region

    Parameters
    ----------
    image : NumPy array of ints
        Input image array
    polygon_feature : list | NumPy array
        Polygon coordinates defining the region of interest

    Returns
    -------
    mask : MaskedArray
        NumPy masked array where the pixels within 
        the polygon are masked out 
    """
    (y, x) = get_polygon_coordinates(np.array(polygon_feature))
    rr, cc = polygon(y, x)
    mask = np.ones(image.shape)
    coords_in_mask = (
        (rr >= 0) & (rr < image.shape[0]) & (cc >= 0) & (cc < image.shape[1])
    )
    mask[rr[coords_in_mask], cc[coords_in_mask]] = 0
    return ma.masked_array(image, mask=mask)
