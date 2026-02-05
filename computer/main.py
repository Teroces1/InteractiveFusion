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
        self.pos = pos          # Vector3
        self.radius = radius    # half-size of cube

    def getSignedDistance(self, point):
        # Vector from cube center to point
        p = point - self.pos

        # Distance from each face
        q = Vector3(abs(p.x), abs(p.y), abs(p.z)) - Vector3(self.radius, self.radius, self.radius)

        # Outside distance
        outside = Vector3(max(q.x, 0), max(q.y, 0), max(q.z, 0)).magnitude()

        # Inside distance (negative)
        inside = min(max(q.x, max(q.y, q.z)), 0)

        return outside + inside



def distance2analog(distanceMM):
    # assuming this value is projected on the normal vector of the model
    if distance2analog < 0:
        return 255
    return max(min(int(128 - 4*distance2analog), 128), 0)



