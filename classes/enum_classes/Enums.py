from enum import Enum

class ImageResolution(Enum):
    UHD = (3840, 2160)
    FHD = (1920, 1080)
    HD = (720, 480)
    SD = (640, 360)
