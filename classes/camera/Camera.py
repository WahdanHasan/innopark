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
        self.ChangeFeed(rtsp_link=rtsp_link)

        # Set default scaled resolution
        self.default_resolution = ImageResolution.SD.value

        # Define variables
        self.frame = 0

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

    def StoreNextFrame(self):
        # Gets and stores the next frame
        # It should be noted that this function is to be called with the primary loop only.
        # All processes that wish to use the current frame should use GetCurrentFrame

        _, self.frame = self.feed.read()
        self.frame = IU.RescaleImageToResolution(img=self.frame,
                                                 new_dimensions=self.default_resolution)

    def GetCurrentFrame(self):
        return self.frame

    def IsFeedActive(self):
        return self.feed.isOpened()

    def ChangeFeed(self, rtsp_link):
        # Changes the rtsp link for the camera feed

        self.rtsp_link = rtsp_link

        self.feed = cv2.VideoCapture(rtsp_link)

        if not self.feed.isOpened():
            print('[ERROR]: camera with id ' + self.camera_id + " failed to start.", file=sys.stderr)
            return

    def ReleaseFeed(self):
        # Releases the rtsp link for the camera feed

        self.feed.release()

# Development only functions

    def GetRawLoopingNextFrame(self):
        # To be used when dealing with videos during development/demos.
        # Loops the footage when it finishes
        # Returns the next frame

        ret, frame = self.feed.read()

        if not ret:
            self.feed = cv2.VideoCapture(self.rtsp_link)
            ret, frame = self.feed.read()

        return frame

    def GetScaledLoopingNextFrame(self):
        # To be used when dealing with videos during development/demos.
        # Loops the footage when it finishes
        # Returns the next frame after scaling it



        ret, frame = self.feed.read()

        if not ret:
            self.feed = cv2.VideoCapture(self.rtsp_link)
            ret, frame = self.feed.read()

        frame = IU.RescaleImageToResolution(img=frame,
                                            new_dimensions=self.default_resolution)


        return frame






