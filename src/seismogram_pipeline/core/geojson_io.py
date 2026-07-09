import geojson
import json
from .debug import Debug
import numpy as np


def convert_numpy(obj):
    if isinstance(obj, dict):
        return {k: convert_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy(v) for v in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj


def get_features(filename):
    with open(filename, "r") as myfile:
        data = myfile.read()
        features = geojson.loads(data)
        return features


def save_features(features, filename):
    if Debug.active:
        indent = 2
    else:
        indent = None

    with open(filename, "w") as outfile:
        # geojson.dump(features, outfile, indent=indent)
        geojson.dump(convert_numpy(features), outfile, indent=indent)


def save_json(dict, filename):
    if Debug.active:
        indent = 2
    else:
        indent = None

    with open(filename, "w") as outfile:
        json.dump(dict, outfile, indent=indent)
