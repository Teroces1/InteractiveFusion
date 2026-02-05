# import leap
from arduino import Arduino, Port
import serial.tools.list_ports
from vector import Vector3
from renderer import Cube, Sphere, Camera, Renderer3D
import numpy as np
import math

sin, cos = math.sin, math.cos


if __name__ == "__main__":
    # Toggle between Cube and Sphere
    shape = Cube([0,0,0], 80)
    # shape = Sphere([0,0,0], 80)

    cam = Camera(distance=400, angle=0)
    renderer = Renderer3D()

    def moving_point(t):
        return np.array([
            130 * cos(t * 0.03),
            60 * sin(t * 0.05),
            130 * sin(t * 0.03)
        ])

    renderer.render(shape, cam, moving_point)


def distance2analog(distanceMM):
    # assuming this value is projected on the normal vector of the model
    if distance2analog < 0:
        return 255
    return max(min(int(128 - 4*distance2analog), 128), 0)



