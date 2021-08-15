import cv2
import sys
from imutils.video import VideoStream
import classes.system_utilities.image_utilities.ImageUtilities as IU
from classes.enum_classes.Enums import ImageResolution

class Camera:
    def __init__(self, rtsp_link, camera_id, buffer_size=1):
        # Assign local variables
        self.rtsp_link = rtsp_link
        self.camera_id = camera_id
        self.default_resolution = ImageResolution.SD.value

        # Link validation
        if not (isinstance(rtsp_link, str) or isinstance(rtsp_link, int)):
            print('[ERROR]: camera RTSP link must be of string or integer datatype.', file=sys.stderr)
            return

        # Start camera feed
        self.feed = 0
        self.UpdateFeed(rtsp_link=rtsp_link)

    def UpdateFeed(self, rtsp_link): # This function is not thread safe atm. This should be rectified.
        # Changes the rtsp link for the camera feed

        self.rtsp_link = rtsp_link

        self.feed = VideoStream(rtsp_link)

        self.feed.start()

        # if not self.feed.isOpened():
        #     print('[ERROR]: camera with id ' + str(self.camera_id) + " failed to start.", file=sys.stderr)


    def ReleaseFeed(self):
        # Releases the rtsp link for the camera feed

        self.feed.stop()

    def GetRawNextFrame(self):
        # Returns the next frame from the feed queue

        frame = self.feed.read()

        return frame

    def GetScaledNextFrame(self):
        # Returns the next frame from the feed queue post scaling based on the default scale factor

        frame = self.feed.read()

        frame = IU.RescaleImageToResolution(img=frame,
                                            new_dimensions=self.default_resolution)

        return frame







