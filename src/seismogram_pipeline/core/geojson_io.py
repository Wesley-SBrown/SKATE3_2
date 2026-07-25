import geojson
from geojson import FeatureCollection
import json
from .debug import Debug
import numpy as np
from typing import Any

def convert_numpy(obj: Any) -> Any:
    """
    Convert input object data type(s) from NumPy to built-in types

    Parameters
    ----------
    obj : Any
        Object of a NumPy type

    Returns
    -------
    obj : Any
        object of standard python built-in type(s)
    """
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
    elif isinstance(obj, np.bool_):
        return bool(obj)
    else:
        return obj


def get_features(filename: str) -> FeatureCollection:
    """
    Retrieves the features from a given input file

    Parameters
    ----------
    filename : str
        Input file name

    Returns
    -------
    features : FeatureCollection
        GeoJSON Feature Collection from file
    """
    with open(filename, "r") as myfile:
        data = myfile.read()
        features = geojson.loads(data)
        return features


def save_features(
    features: FeatureCollection, 
    filename: str
) -> None:

    """
    Writes a GeoJSON feature collection to the output filename

    Parameters
    ----------
    features : FeatureCollection
        Input GeoJSON feature collection
    filename : str
        Output file name
    """
    if Debug.active:
        indent = 2
    else:
        indent = None

    with open(filename, "w") as outfile:
        # geojson.dump(features, outfile, indent=indent)
        geojson.dump(convert_numpy(features), outfile, indent=indent)


def save_json(data: dict[str, Any], filename: str) -> None:
    """
    Writes a dictionary object to the input filename

    Parameters
    ----------
    data : dict
        Input dictionary object
    filename : str
        Ouput file name
    """
    if Debug.active:
        indent = 2
    else:
        indent = None

    with open(filename, "w") as outfile:
        json.dump(data, outfile, indent=indent)
