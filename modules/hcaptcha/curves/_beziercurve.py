import math

class BezierCurve():
    @staticmethod
    def binomial(n, k):
        """Returns the binomial coefficient "n choose k" """
        return math.factorial(n) / float(math.factorial(k) * math.factorial(n - k))

    @staticmethod
    def bernsteinPolynomialPoint(x, i, n):
        """Calculate the i-th component of a bernstein polynomial of degree n"""
        return BezierCurve.binomial(n, i) * (x ** i) * ((1 - x) ** (n - i))

    @staticmethod
    def bernsteinPolynomial(points):
        """
        Given list of control points, returns a function, which given a point [0,1] returns
        a point in the bezier curve described by these points
        """
        def bern(t):
            n = len(points) - 1
            x = y = 0
            for i, point in enumerate(points):
                bern = BezierCurve.bernsteinPolynomialPoint(t, i, n)
                x += point[0] * bern
                y += point[1] * bern
            return x, y
        return bern

    @staticmethod
    def curvePoints(n, points):
        """
        Given list of control points, returns n points in the bezier curve,
        described by these points
        """
        curvePoints = []
        bernstein_polynomial = BezierCurve.bernsteinPolynomial(points)
        for i in range(n):
            t = i / (n - 1)
            curvePoints += bernstein_polynomial(t),
        return curvePoints
