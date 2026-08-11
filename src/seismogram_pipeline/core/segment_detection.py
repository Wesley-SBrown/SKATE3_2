from .timer import timeStart, timeEnd

import numpy as np
from numpy.random import rand, randint
from numpy.typing import NDArray
from typing import Any
import geojson
import math

Point2D = tuple[int, int]

def get_segments(
    image: NDArray[np.generic], 
    intersections: Any, 
    num_traces: int = 24, 
    max_freq_multiplier: int = 20,
    min_amplitude: int = 10, 
    amplitude_divisor: int = 4, 
    offset_divisor: int = 4
) -> list[list[Point2D]]:
    """
    Generate dummy trace segments modeled as sinusoidal waves across the image width

    Parameters
    ----------
    image : NDArray[np.generic]
        The input image used to determine shape boundaries for segment generation
    intersections : Any
        Intersection points or constraints (reserved for future functionality)
    num_traces : int, optional, default 24
        The number of trace segments to generate
    max_freq_multiplier : int, optional, default 20
        The maximum frequency multiplier for random wave generation
    min_amplitude : int, optional, default 10
        The minimum amplitude value for the waves
    amplitude_divisor : int, optional, default 4
        The divisor used to determine the maximum amplitude relative to image height
    offset_divisor : int, optional, default 4
        The divisor used to determine the minimum vertical offset relative to image height

    Returns
    -------
    list[list[Point2D]]
        A list of generated traces, where each trace is a list of 2D coordinate points (x, y)
    """
    # TODO: add functionality for `intersections`
    # Generate dummy segments
    def random_phase():
        return rand() * math.pi * 2

    def random_freq():
        return randint(1, max_freq_multiplier) * math.pi * 2 / shape[1]

    def random_amplitude():
        return randint(min_amplitude, shape[0] / amplitude_divisor)

    def random_offset():
        return randint(shape[0] / offset_divisor, shape[0])

    shape = image.shape
    line_array = []
    for _ in range(num_traces):
        phase_1, phase_2 = random_phase(), random_phase()
        freq_1, freq_2 = random_freq(), random_freq()
        amp_1, amp_2 = random_amplitude(), random_amplitude()
        offset = random_offset()
        line_array.append(
            [
                (
                    x,
                    offset
                    + int(
                        amp_1 * math.sin(x * freq_1 + phase_1)
                        + amp_2 * math.sin(x * freq_2 + phase_2)
                    ),
                )
                for x in range(shape[1])
            ]
        )

    return line_array


def save_segments_as_geojson(
    segments: list[list[Point2D]], 
    filepath: str
) -> None:
    """
    Save a collection of trace segments as a GeoJSON FeatureCollection file

    Parameters
    ----------
    segments : list[list[Point2D]]
        A list of trace segments, where each segment is a list of 2D coordinate points (x, y)
    filepath : str
        The path and filename where the GeoJSON file should be saved
    """
    timeStart("saving to " + str(filepath))
    features = [
        geojson.Feature(geometry=geojson.LineString(line), id=idx)
        for idx, line in enumerate(segments)
    ]
    collection = geojson.FeatureCollection(features)
    with open(filepath, "w") as outfile:
        geojson.dump(collection, outfile)
    timeEnd("saving to " + str(filepath))
