import classes.system_utilities.image_utilities.ImageUtilities as IU
from classes.system_utilities.helper_utilities import Constants

import sys
from imutils.video import VideoStream

class Camera:
    def __init__(self, rtsp_link, camera_id, name=""):
        # Assign local variables
        self.rtsp_link = rtsp_link
        self.camera_id = camera_id
        self.name = name
        self.default_resolution = Constants.default_camera_shape[:2]

        # Link validation
        if not (isinstance(rtsp_link, str) or isinstance(rtsp_link, int)):
            print('[ERROR]: camera RTSP link must be of string or integer datatype.', file=sys.stderr)
            return

        # Start camera feed
        self.feed = 0
        self.UpdateFeed(rtsp_link=rtsp_link)

        print('Started camera with id ' + str(self.camera_id))

    def UpdateFeed(self, rtsp_link):
        # Changes the rtsp link for the camera feed

        self.rtsp_link = rtsp_link

        self.feed = VideoStream(rtsp_link)

        self.feed.start()

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







