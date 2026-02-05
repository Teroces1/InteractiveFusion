import serial
import time
from enum import Enum

class Port(Enum):
    COM8 = 8,
    COM9 = 9

_portConv = {8: "COM8", 9: "COM9"}

class Arduino:
    def __init__(self, port: Port = Port.COM9):
        self. port = port
        self.ser = serial.Serial(_portConv.get(port, None))

    def sendInt(self, data: int):
        self.ser.write(f"{data}\n".encode())
