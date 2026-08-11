import json
from typing import Any

class Record:
    """
    A utility class for recording and exporting application statistics and metrics to JSON files
    """
    active = False
    stats = {}

    @classmethod
    def activate(cls) -> None:
        """
        Activate the recording utility
        """
        cls.active = True

    @classmethod
    def record(cls, key: str, value: Any) -> None:
        """
        Record a statistic under a specified key

        Parameters
        ----------
        key : str
            The identifier/name of the statistic to record
        value : Any
            The value associated with the statistic
        """
        cls.stats[key] = value

    @classmethod
    def export_as_json(cls, filename: str) -> None:
        """
        Export current recorded stats, appending them to an existing JSON record file or creating a new one

        Parameters
        ----------
        filename : str
            The filename of the JSON file where stats should be exported
        """
        try:
            with open(filename, "r+") as myfile:
                data = myfile.read()
                prev_stats = json.loads(data)
        except IOError:
            # no previous stats recorded, so
            # initialize an empty dict of stats
            prev_stats = {key: [] for key in cls.stats}

        # append all the new stats to the old stats
        for key, record in cls.stats.items():
            try:
                prev_stats[key].append(record)
            except KeyError:
                print(
                    f"WARN: Failed to save a new statistic, {key}, to an existing record")

        with open(filename, "w") as myfile:
            json.dump(prev_stats, myfile)
