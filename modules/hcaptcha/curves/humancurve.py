import pytweening
import numpy as np
import random
from ._utils import isListOfPoints, isNumeric
from ._beziercurve import BezierCurve

def gen_mouse_move(from_point, to_point, time, **kwargs):
    obj = HumanCurve(from_point, to_point, time, **kwargs)
    return obj.points

class HumanCurve():
    """
    Generates a human-like mouse curve starting at given source point,
    and finishing in a given destination point
    """

    def __init__(self, fromPoint, toPoint, time, **kwargs):
        self.fromPoint = fromPoint
        self.toPoint = toPoint
        points = self.generateCurve(**kwargs)
        points = list(dict.fromkeys([
            (int(x), int(y))
            for x,y in points
        ]))
        self.points = []
        for x, y in points:
            time.ms_sleep(random.randint(5, 15))
            t = time.ms_time()
            self.points.append((x, y, t))


    def generateCurve(self, **kwargs):
        """
        Generates a curve according to the parameters specified below.
        You can override any of the below parameters. If no parameter is
        passed, the default value is used.
        """
        offsetBoundaryX = kwargs.get("offsetBoundaryX", 100)
        offsetBoundaryY = kwargs.get("offsetBoundaryY", 100)
        leftBoundary = kwargs.get("leftBoundary", min(self.fromPoint[0], self.toPoint[0])) - offsetBoundaryX
        rightBoundary = kwargs.get("rightBoundary", max(self.fromPoint[0], self.toPoint[0])) + offsetBoundaryX
        downBoundary = kwargs.get("downBoundary", min(self.fromPoint[1], self.toPoint[1])) - offsetBoundaryY
        upBoundary = kwargs.get("upBoundary", max(self.fromPoint[1], self.toPoint[1])) + offsetBoundaryY
        knotsCount = kwargs.get("knotsCount", 2)
        distortionMean = kwargs.get("distortionMean", 1)
        distortionStdev = kwargs.get("distortionStdev", 1)
        distortionFrequency = kwargs.get("distortionFrequency", 0.5)
        tween = kwargs.get("tweening", pytweening.easeOutQuad)
        targetPoints = kwargs.get("targetPoints", 100)

        internalKnots = self.generateInternalKnots(leftBoundary,rightBoundary, \
            downBoundary, upBoundary, knotsCount)
        points = self.generatePoints(internalKnots)
        points = self.distortPoints(points, distortionMean, distortionStdev, distortionFrequency)
        points = self.tweenPoints(points, tween, targetPoints)
        return points

    def generateInternalKnots(self, \
        leftBoundary, rightBoundary, \
        downBoundary, upBoundary,\
        knotsCount):
        """
        Generates the internal knots used during generation of bezier curvePoints
        or any interpolation function. The points are taken at random from
        a surface delimited by given boundaries.
        Exactly knotsCount internal knots are randomly generated.
        """
        if not (isNumeric(leftBoundary) and isNumeric(rightBoundary) and
            isNumeric(downBoundary) and isNumeric(upBoundary)):
            raise ValueError("Boundaries must be numeric")
        if not isinstance(knotsCount, int) or knotsCount < 0:
            raise ValueError("knotsCount must be non-negative integer")
        if leftBoundary > rightBoundary:
            raise ValueError("leftBoundary must be less than or equal to rightBoundary")
        if downBoundary > upBoundary:
            raise ValueError("downBoundary must be less than or equal to upBoundary")

        knotsX = np.random.choice(range(leftBoundary, rightBoundary), size=knotsCount)
        knotsY = np.random.choice(range(downBoundary, upBoundary), size=knotsCount)
        knots = list(zip(knotsX, knotsY))
        return knots

    def generatePoints(self, knots):
        """
        Generates bezier curve points on a curve, according to the internal
        knots passed as parameter.
        """
        if not isListOfPoints(knots):
            raise ValueError("knots must be valid list of points")

        midPtsCnt = max( \
            abs(self.fromPoint[0] - self.toPoint[0]), \
            abs(self.fromPoint[1] - self.toPoint[1]), \
            2)
        knots = [self.fromPoint] + knots + [self.toPoint]
        return BezierCurve.curvePoints(midPtsCnt, knots)

    def distortPoints(self, points, distortionMean, distortionStdev, distortionFrequency):
        """
        Distorts the curve described by (x,y) points, so that the curve is
        not ideally smooth.
        Distortion happens by randomly, according to normal distribution,
        adding an offset to some of the points.
        """
        if not(isNumeric(distortionMean) and isNumeric(distortionStdev) and \
               isNumeric(distortionFrequency)):
            raise ValueError("Distortions must be numeric")
        if not isListOfPoints(points):
            raise ValueError("points must be valid list of points")
        if not (0 <= distortionFrequency <= 1):
            raise ValueError("distortionFrequency must be in range [0,1]")

        distorted = []
        for i in range(1, len(points)-1):
            x,y = points[i]
            delta = np.random.normal(distortionMean, distortionStdev) if \
                random.random() < distortionFrequency else 0
            distorted += (x,y+delta),
        distorted = [points[0]] + distorted + [points[-1]]
        return distorted

    def tweenPoints(self, points, tween, targetPoints):
        """
        Chooses a number of points(targetPoints) from the list(points)
        according to tweening function(tween).
        This function in fact controls the velocity of mouse movement
        """
        if not isListOfPoints(points):
            raise ValueError("points must be valid list of points")
        if not isinstance(targetPoints, int) or targetPoints < 2:
            raise ValueError("targetPoints must be an integer greater or equal to 2")

        # tween is a function that takes a float 0..1 and returns a float 0..1
        res = []
        for i in range(targetPoints):
            index = int(tween(float(i)/(targetPoints-1)) * (len(points)-1))
            res += points[index],
        return res
