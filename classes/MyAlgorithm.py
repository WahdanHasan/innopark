import threading
import time
from datetime import datetime
import cv2
import numpy as np

time_cycle = 80


class MyAlgorithm(threading.Thread):

    def __init__(self, camera):
        self.camera = camera

        self.stop_event = threading.Event()
        self.kill_event = threading.Event()
        self.lock = threading.Lock()
        threading.Thread.__init__(self, args=self.stop_event)

    def run(self):

        self.stop_event.clear()

        while (not self.kill_event.is_set()):

            start_time = datetime.now()

            if not self.stop_event.is_set():
                self.execute()

            finish_Time = datetime.now()

            dt = finish_Time - start_time
            ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
            # print (ms)
            if (ms < time_cycle):
                time.sleep((time_cycle - ms) / 1000.0)

    def stop(self):
        self.stop_event.set()

    def play(self):
        if self.is_alive():
            self.stop_event.clear()
        else:
            self.start()

    def kill(self):
        self.kill_event.set()

    def execute(self):
        # Getting the first frame
        # We are going to find the strongest corners using goodFeaturesToTrack function
        _, frame1 = self.camera.read()
        frame1_gray = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        p0 = cv2.goodFeaturesToTrack(frame1_gray, 100, 0.01, 10, None, None, 7)

        lin = np.zeros_like(frame1)
        t = 0
        while (1):
            # We do the same with the next frame
            t = t + 1
            _, frame2 = self.camera.read()

            frame2 = cv2.medianBlur(frame2, 5)
            # frame_canny = cv2.Canny(frame,200,300)
            frame2_gray = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

            p1, st, err = cv2.calcOpticalFlowPyrLK(frame1_gray, frame2_gray, p0, None,
                                                   None, None,
                                                   (30, 30), 2,
                                                   (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
            for i, (f2, f1) in enumerate(zip(p1, p0)):
                a, b = f2.ravel()
                c, d = f1.ravel()
                frame2 = cv2.circle(frame2, (int(a), int(b)), 5, (0, 0, 255), -1)
                frame2 = cv2.circle(frame2, (int(c), int(d)), 5, (255, 0, 0), -1)
                lin = cv2.line(lin, (int(a), int(b)), (int(c), int(d)), (0, 255, 0), 1)

            if t == 2:
                # Drawing the lines every two frames
                lin = np.zeros_like(frame1)
                t = 0
            img = cv2.add(frame2, lin)

            # if img is not None:
            #     self.camera.setColorImage(img)
            cv2.imshow("Frame", img)
            # We have to upload the values
            frame1_gray = np.copy(frame2_gray)
            p0 = cv2.goodFeaturesToTrack(frame1_gray, 100, 0.01, 10, None, None, 7)

        # self.camera.setThresoldImage(bk_image)