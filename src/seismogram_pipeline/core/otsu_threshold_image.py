from skimage.filters import threshold_otsu
from numpy.ma.core import MaskedArray
import numpy.typing as npt
from numpy import intp, bool_
from numpy.ma import MaskedArray
from typing import Union

def otsu_threshold_image(
    grayscale_image: Union[npt.NDArray[intp], MaskedArray] 
) -> npt.NDArray[bool_]:
    """
    Apply Otsu's thresholding method to a grayscale or masked image

    Parameters
    ----------
    grayscale_image : NumPy array of ints | MaskedArray
        Input grayscale or MaskedArray image
    
    Returns
    -------
    black_and_white_image : NumPy array of bools
        A boolean black & white image. 
        True = above Otsu's threshold
    """
    if type(grayscale_image) is MaskedArray:
        threshold_value = threshold_otsu(grayscale_image.compressed())
    else:
        threshold_value = threshold_otsu(grayscale_image)
    black_and_white_image = grayscale_image > threshold_value
    return black_and_white_image
