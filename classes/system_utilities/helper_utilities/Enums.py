from enum import Enum

class ImageResolution(Enum):
    UHD = (3840, 2160)
    FHD = (1920, 1080)
    HD = (1280, 720)
    SD = (720, 480)
    NTSC = (320, 240)
    QCIF = (176, 144)

class TrackedObjectStatus(Enum):
    MOVING = 0
    STATIONARY = 1
    BB_UPDATED = 2

class EntrantSide(Enum):
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"

class TrackerToTrackedObjectInstruction(Enum):
    STOP_TRACKING = -1
    OBJECT_MOVING = 1
    OBJECT_STATIONARY = 2
    STORE_NEW_ID = 3
    STORE_NEW_BB = 4

class ParkingStatus(Enum):
    OCCUPIED = True
    NOT_OCCUPIED = False

class ObjectToPoolManagerInstruction(Enum):
    GET_ALL_PROCESSES = 1
    GET_LATEST_PROCESS = 2
    GET_PROCESS = 3
    RETURN_PROCESS = 4

class TrackedObjectToBrokerInstruction(Enum):
    GET_VOYAGER = 1
    PUT_VOYAGER = 2

class DetectedObjectAtEntrance(Enum):
    DETECTED = 1
    DETECTED_WITH_YOLO = 2
    NOT_DETECTED = -1


class ShutDownEvent(Enum):
    SHUTDOWN = 1

class YoloModel(Enum):
    YOLOV3 = 0,
    YOLOV4 = 1,
    LICENSE_DETECTOR = 2

class ODProcessInstruction(Enum):
    IMAGE_PROVIDED = 0

class ReturnStatus(Enum):
    SUCCESS = 0
    FAIL = 1