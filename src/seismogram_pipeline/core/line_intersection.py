# from http://stackoverflow.com/questions/3252194/numpy-and-line-intersections
#
# line segment intersection using vectors
# see Computer Graphics by F.S. Hill
#
from numpy import dot, empty_like, ndarray
from typing import Union, Optional

def perp(a: ndarray) -> ndarray:
    """
    Calculates a perpendicular vector in a 2D Cartesian coordinate system

    Parameters
    ----------
    a : ndarray 
        2-D vector

    Returns
    -------
    b : ndarray
        Perpendicular vector
    """
    b = empty_like(a)
    b[0] = -a[1]
    b[1] = a[0]
    return b


# seg_intersect returns the intersection (if any) of the infinite lines
# defined by segments seg1 and seg2

# seg1 and seg2 are each of the form [[x1, y1], [x2, y2]]

def seg_intersect(
    seg1: Union[list, ndarray], 
    seg2: Union[list, ndarray]
) -> Optional[ndarray]:
    """
    Calculates the intersection of infinite lines (if any)

    seg1 : list or ndarray
        Segment 1 [[x1, y1], [x2, y2]]
    seg2 : list or ndarray
        Segment 2 [[x1, y1], [x2, y2]]

    Returns
    -------
    intersection : ndarray, optional
        Intersection of the two segments (if any)
        Returns None if parallel
    """
    a1, a2, b1, b2 = seg1[0], seg1[1], seg2[0], seg2[1]
    da = a2 - a1
    db = b2 - b1,
    dp = a1 - b1
    dap = perp(da)
    denom = dot(dap, db)
    num = dot(dap, dp)

    # handle parallel lines
    if denom == 0:
        return None
    
    return (num / denom.astype(float)) * db + b1 
