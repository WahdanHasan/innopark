import cv2
import sys
import classes.system_utilities.image_utilities.ImageUtilities as IU
from classes.enum_classes.Enums import ImageResolution

class Camera:
    def __init__(self, rtsp_link, camera_id):
        # Assign local variables
        self.rtsp_link = rtsp_link
        self.camera_id = camera_id

        # Link validation
        if not (isinstance(rtsp_link, str) or isinstance(rtsp_link, int)):
            print('[ERROR]: camera RTSP link must be of string or integer datatype.', file=sys.stderr)
            return

        # Start camera feed
        self.feed = cv2.VideoCapture(rtsp_link)

        if not self.feed.isOpened():
            print('[ERROR]: camera with id ' + self.camera_id + " failed to start.", file=sys.stderr)
            return

    def GetRawNextFrame(self):
        # Returns the next frame from the video source

         _, frame = self.feed.read()

         return frame

    def GetScaledNextFrame(self):
        # Returns the next frame from the video source post scaling based on the default scale factor

        default_resolution = ImageResolution.SD.value

        _, frame = self.feed.read()

        frame = IU.RescaleImageToResolution(img=frame,
                                            new_dimensions=default_resolution)

        return frame






