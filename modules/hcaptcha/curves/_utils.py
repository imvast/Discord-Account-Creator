import numpy as np

def isNumeric(val):
    return isinstance(val, (float, int, np.int32, np.int64, np.float32, np.float64))

def isListOfPoints(l):
    if not isinstance(l, list):
        return False
    try:
        isPoint = lambda p: ((len(p) == 2) and isNumeric(p[0]) and isNumeric(p[1]))
        return all(map(isPoint, l))
    except (KeyError, TypeError) as e:
        return False