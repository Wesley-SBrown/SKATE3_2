import sys
from time import time

timeDict: dict[str, float] = {}
depth: int = 0

# keep track of whether timers are being nested
timer_open: bool = False


def timeStart(key: str) -> None:
    """
    Starts a timer for a specifc operation and prints the starting message.

    Parameters
    ----------
    key : str
        Operation name
    """
    global depth, timer_open

    timeDict[key] = time()

    printStart(key, timer_open)

    depth += 1
    timer_open = True


def timeEnd(key: str) -> float:
    """
    Ends timer for specific operation

    Parameters
    ----------
    key : str
        Operation name
    """
    global depth, timer_open

    depth -= 1

    time_elapsed = time() - timeDict[key]
    del timeDict[key]

    printEnd(key, time_elapsed, timer_open)

    timer_open = False

    return time_elapsed


def printStart(key: str, timer_open: bool) -> None:
    """
    Prints start message

    Parameters
    ----------
    key : str
        Operation name
    timer_open : bool
        Flag for whether nested timer is currently open
    """
    if timer_open is True:
        sys.stdout.write("\n")

    sys.stdout.write(getIndent() + key + " ... ")
    sys.stdout.flush()


def printEnd(key: str, time_elapsed: float, timer_open: bool) -> None:
    """
    Prints the elapsed time for a completed operation.

    Parameters
    ----------
    key : str
        The identifier/name for the timing operation.
    time_elapsed : float
        The total time elapsed in seconds.
    timer_open : bool
        Flag indicating if a nested timer is currently open.
    """
    if timer_open is False:
        sys.stdout.write(getIndent())

    sys.stdout.write(str(time_elapsed) + "s \n")


def getIndent() -> str:
    """
    Generates indentation string based upon current nested depth

    Returns
    -------
    indent : str
        String of spaces representing the current depth
    """
    return "".join(["  " for i in range(depth)])
