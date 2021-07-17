import cv2
import sys

class Camera:
    def __init__(self, rtsp_link, camera_id):
        # Assign local variables
        self.rtsp_link = rtsp_link
        self.camera_id = camera_id

        # Link validation
        # print(type(rtsp_link), isinstance(rtsp_link, str))
        if not (isinstance(rtsp_link, str) or isinstance(rtsp_link, int)):
            print('[ERROR]: Camera RTSP link must be of string or integer datatype.', file=sys.stderr)
            return

        # Start camera feed
        self.feed = cv2.VideoCapture(rtsp_link)

        if not self.feed.isOpened():
            print('[ERROR]: Camera with id ' + self.camera_id + " failed to start.", file=sys.stderr)
            return

    def GetNextFrame(self):
         _, frame = self.feed.read()

         return frame



