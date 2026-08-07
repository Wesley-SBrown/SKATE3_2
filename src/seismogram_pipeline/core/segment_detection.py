from .timer import timeStart, timeEnd

from numpy.random import rand, randint
import geojson
import math


def get_segments(
    image, intersections, num_traces = 24, max_freq_multiplier = 20,
    min_amplitude = 10, amplitude_divisor = 4, offset_divisor = 4
):
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


def save_segments_as_geojson(segments, filepath):
    timeStart("saving to " + str(filepath))
    features = [
        geojson.Feature(geometry=geojson.LineString(line), id=idx)
        for idx, line in enumerate(segments)
    ]
    collection = geojson.FeatureCollection(features)
    with open(filepath, "w") as outfile:
        geojson.dump(collection, outfile)
    timeEnd("saving to " + str(filepath))
