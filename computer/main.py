def distance2analog(distanceMM):
    # assuming this value is projected on the normal vector of the model
    if distance2analog < 0:
        return 255
    return max(min(int(128 - 4*distance2analog), 128), 0)