from __future__ import annotations
import math

class Vector3:
    __slots__ = ("x", "y", "z")

    def __init__(self, x: float, y: float, z: float):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    # ---------- Representation ----------
    def __repr__(self):
        return f"Vector3({self.x}, {self.y}, {self.z})"

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    # ---------- Basic arithmetic ----------
    def __add__(self, other: Vector3):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Vector3):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __neg__(self):
        return Vector3(-self.x, -self.y, -self.z)

    # Scalar multiplication
    def __mul__(self, scalar: float):
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    __rmul__ = __mul__

    # Scalar division
    def __truediv__(self, scalar: float):
        return Vector3(self.x / scalar, self.y / scalar, self.z / scalar)

    # ---------- Dot & cross ----------
    def dot(self, other: Vector3):
        return self.x * other.x + self.y * other.y + self.z * other.z

    def __matmul__(self, other: Vector3):
        return self.dot(other)

    def cross(self, other: Vector3):
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )

    # ---------- Magnitude & normalization ----------
    def magnitude(self):
        return math.sqrt(self.x*self.x + self.y*self.y + self.z*self.z)

    def magnitude_squared(self):
        return self.x*self.x + self.y*self.y + self.z*self.z

    def normalized(self):
        m = self.magnitude()
        if m == 0:
            return Vector3(0, 0, 0)
        return self / m

    # ---------- Projection & rejection ----------
    def project_onto(self, other: Vector3):
        denom = other.magnitude_squared()
        if denom == 0:
            return Vector3(0, 0, 0)
        return other * (self.dot(other) / denom)

    def reject_from(self, other: Vector3):
        return self - self.project_onto(other)

    # ---------- Distance ----------
    def distance_to(self, other: Vector3):
        return (self - other).magnitude()

    def distance_squared_to(self, other: Vector3):
        return (self - other).magnitude_squared()

    # ---------- Equality ----------
    def __eq__(self, other: object):
        if not isinstance(other, Vector3):
            return NotImplemented
        return (
            math.isclose(self.x, other.x) and
            math.isclose(self.y, other.y) and
            math.isclose(self.z, other.z)
        )
