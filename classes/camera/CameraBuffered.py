import classes.system_utilities.image_utilities.ImageUtilities as IU
from classes.system_utilities.helper_utilities import Constants

import numpy as np
import cv2
import sys
from queue import Queue
from threading import Thread

class Camera:
    def __init__(self, rtsp_link, camera_id, buffer_size=1):
        # Assign local variables
        self.rtsp_link = rtsp_link
        self.camera_id = camera_id
        self.default_resolution = Constants.default_camera_shape[:2]
        self.base_blank = np.zeros(shape=(Constants.default_camera_shape[1], Constants.default_camera_shape[0], Constants.default_camera_shape[2]), dtype=np.uint8)


        # Link validation
        if not (isinstance(rtsp_link, str) or isinstance(rtsp_link, int)):
            print('[ERROR]: camera RTSP link must be of string or integer datatype.', file=sys.stderr)
            return

        # Start camera feed
        self.feed = 0
        self.UpdateFeed(rtsp_link=rtsp_link)

        # LIFO Queue threading initializations and start
        self.frame = 0
        self.queue_buffer_size = buffer_size
        self.frame_queue = Queue(maxsize=buffer_size)
        self.feed_stopped = False
        self.StartFeedThread()

    def StartFeedThread(self):
        # Start a daemon thread to keep polling the camera

        polling_thread = Thread(target=self.PollFeedThread, args=())
        polling_thread.daemon = True
        polling_thread.start()


        return self

    def PollFeedThread(self):
        # For use by a thread to keep polling the camera feed until stopped

        while not self.feed_stopped:

            _, frame = self.feed.read()

            # Comment this out if not using video files
            # if not _:
            #     self.UpdateFeed(self.rtsp_link)
            #     continue

            self.frame_queue.put(frame)

    def UpdateFeed(self, rtsp_link): # This function is not thread safe atm. This should be rectified.
        # Changes the rtsp link for the camera feed

        self.rtsp_link = rtsp_link

        self.feed = cv2.VideoCapture(rtsp_link)

        if not self.feed.isOpened():
            print('[ERROR]: camera with id ' + str(self.camera_id) + " failed to start.", file=sys.stderr)

    def StopFeedThread(self):
        # Stop the current feed

        self.feed_stopped = True

    def ReleaseFeed(self):
        # Releases the rtsp link for the camera feed

        self.StopFeedThread()
        self.feed.release()

    def IsFeedActive(self):
        return self.feed.isOpened()

    def GetRawNextFrame(self):
        # Returns the next frame from the feed queue

        frame = self.frame_queue.get()

        return frame

    def GetScaledNextFrame(self):
        # Returns the next frame from the feed queue post scaling based on the default scale factor

        frame = self.frame_queue.get()

        try:
            frame = IU.RescaleImageToResolution(img=frame,
                                                new_dimensions=self.default_resolution)
        except cv2.error as cv2_error:
            # if cv2_error == '!ssize.empty()':
            frame = self.base_blank
        return frame
