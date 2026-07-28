# -*- coding: utf-8 -*-
"""
Created on Sun Nov  9 21:53:26 2014

@author: benamy
"""

import numpy as np
import numpy.typing as npt
from math import sqrt
from .debug import Debug
from typing import Union

generator = Debug.random


def best_candidate_sample(
    coords: npt.NDArray[np.intp], 
    num_samples: int, 
    num_candidates: int = 10
  ) -> npt.NDArray[np.intp]:
    """
    Sample points randomly from a 2-D array using Mitchell's Best Candidate
    sampling algorithm. Produces more even coverage of an array than simply
    taking a number of uniform random samples.

    Parameters
    ------------
    coords : 2-D array of ints
      A list of candidate points.
    num_samples : int
      The number of samples to take.
    num_candidates : int, optional, default 10
      The number of candidate samples to consider per sample point.

    Returns
    ---------
    samples : 2-D numpy array of ints
      The coordinates of the chosen sample points. The array has two columns
      and num_samples rows.
    """
    samples = [get_candidates(coords, num_candidates)[0]]
    for i in range(1, num_samples):
        candidates = get_candidates(coords, num_candidates)
        best_candidate = find_best_candidate(candidates, samples)
        samples.append(best_candidate)
    samples = np.asarray(samples)
    return samples


def get_candidates(
    coords: npt.NDArray[np.intp], 
    num_candidates : int
) -> npt.NDArray[np.intp]:
    """
    Gets a specified number of random candidates from the input coords array
    
    Parameters
    ----------
    coords : numpy array of ints
      Cotains the transpose of a masked image
    num_candidates : int
      Quanity of random candidates to select

    Returns
    -------
    candidates : NumPy array of ints
      Candidate points to be used in other functions
    """
    random_indices = generator.choice(len(coords), num_candidates)
    candidates = coords[random_indices, :]
    return candidates


def best_candidate_sample_from_rect(
    shape: Union[npt.NDArray[np.intp], tuple[int]], 
    num_samples: int, 
    num_candidates: int = 10
) -> npt.NDArray[np.intp]:
    """
    Sample points randomly from a 2-D array using Mitchell's Best Candidate
    sampling algorithm. Produces more even coverage of an array than simply
    taking a number of uniform random samples.

    Parameters
    ------------
    shape : numpy array or tuple of ints
      The dimensions of the image array.
    num_samples : int
      The number of samples to take.
    num_candidates : int, optional
      The number of candidate samples to consider per sample point.

    Returns
    ---------
    samples : 2-D numpy array of ints
      The coordinates of the chosen sample points. The array has two columns
      and num_samples rows.
    """
    samples = [get_candidates_from_rect(shape, num_candidates)[0]]
    for i in range(1, num_samples):
        candidates = get_candidates_from_rect(shape, num_candidates)
        best_candidate = find_best_candidate(candidates, samples)
        samples.append(best_candidate)
    samples = np.asarray(samples)
    return samples


def get_candidates_from_rect(
    shape: Union[npt.NDArray[np.intp], tuple[int]], 
    num_candidates : int
) -> npt.NDArray[np.intp]:
    """
    Gets a collection of random candidate ints, given a shape boundary

    Parameters
    ----------
    shape: numpy array or tuple of ints
      The dimensions of the image array.
    num_candidates : int, optional
      The number of candidate samples to consider per sample point.

    Returns
    -------
    candidates : NumPy array of ints
      Candidate points from the specified boundary
    """
    candidates = np.zeros((num_candidates, 2), dtype=int)
    candidates[:, 0] = generator.randint(0, high=shape[0], size=num_candidates)
    candidates[:, 1] = generator.randint(0, high=shape[1], size=num_candidates)
    return candidates


def find_best_candidate(
    candidates: npt.NDArray[np.intp], 
    samples: npt.NDArray[np.intp]
) -> npt.NDArray[np.intp]:
    """
    Finds the candidate point that is furthest from any existing sample point

    This function iterates through a set of candidate points, calculates the distance 
    from each candidate to its closest existing sample, and selects the candidate 
    that maximizes this minimum distance (Mitchell's Best Candidate strategy).

    Parameters
    ----------
    candidates : NumPy array of ints
      Collection of candidate points
    samples : 2-D NumPy array of ints
      The coordinates of the chosen sample points. The array has two columns
      and num_samples rows.

    Returns
    -------
    best_candidate : NumPy array of ints
      Candidate that maximizes the minimum distance between its closest sample

    """
    best_candidate = None
    furthest_d = 0
    for candidate in candidates:
        _, dist = find_closest(candidate, samples)
        if dist > furthest_d:
            best_candidate = candidate
            furthest_d = dist
    return best_candidate


def find_closest(
    point: int, 
    points: npt.NDArray[np.intp]
) -> list[int, float]:
    """
    Finds closest point to a sample collection of points

    Parameters
    ----------
    point: int
      Individual integer point
    points: NumPy array of ints
      Collection of sample points

    Returns
    -------
    [closest_p, closest_d] : [int, float]
      A list object containing the cloest point and it's distance
    """
    closest_p = points[0]
    closest_d = distance(point, closest_p)
    for p in points:
        d = distance(point, p)
        if d < closest_d:
            closest_p = p
            closest_d = d
    return [closest_p, closest_d]


def distance(p1: int, p2: int) -> float:
    """
    Calculates the Euclidean distance between 2 points

    Parameters
    ----------
    p1, p2 : int
      Points
    
    Returns
    -------
    distance : float
      Euclidean distance
    """
    return sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)
