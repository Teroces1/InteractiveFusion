# import leap
from arduino import Arduino, Port
import serial.tools.list_ports
from .vector import Vector3


class Sphere:
    def __init__(self, pos, radius):
        self.pos = pos
        self.radius = radius
    
    def getSignedDistance(self, point):
        dist = ((point - self.pos).magnitude() - self.radius)
        return dist

def sign(x):
    if x >= 0:
        return 1
    return -1

class Cube:
    def __init__(self, pos, radius):
        self.pos = pos
        self.radius = radius
    def getSignedDistance(self, point):
        distV = ((point - self.pos).magnitude())

        if abs(distV.x) >= abs(distV.y) and abs(distV.x) >= abs(distV.z):
            normal = Vector3(sign(distV.y), 0, 0)
        elif abs(distV.z) >= abs(distV.y) and abs(distV.z) >= abs(distV.x)
            normal = Vector3(0, 0, sign(distV.y))
        else:
            normal = Vector3(0, sign(distV.y), 0)

        dist = normal.dot(distV) * normal - self.radius

        return dist


def distance2analog(distanceMM):
    # assuming this value is projected on the normal vector of the model
    if distance2analog < 0:
        return 255
    return max(min(int(128 - 4*distance2analog), 128), 0)



