from enum import Enum

class ImageResolution(Enum):
    UHD = (3840, 2160)
    FHD = (1920, 1080)
    HD = (1280, 720)
    SD = (720, 480)
    NTSC = (320, 240)
    QCIF = (176, 144)

class TrackedObjectStatus(Enum):
    Moving = 0
    Stationary = 1

class EntrantSide(Enum):
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"

class ObjectTrackerPipeStatus(Enum):
    CanRead = True


