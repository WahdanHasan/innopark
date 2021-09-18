import classes.system_utilities.image_utilities.ObjectDetection as OD
import classes.system_utilities.image_utilities.ImageUtilities as IU
import cv2
import time
import numpy as np
from multiprocessing import Process, Pipe, Queue, shared_memory
from classes.camera.CameraBuffered import Camera
from classes.helper_classes.Enums import EntrantSide


class EntranceLicenseDetector:

    def StartProcess(self, camera1, camera2):
        # camera is given as type array in the format [camera rtsp, camera id]

        print("[Entrance License] Starting license detector for cameras: " + str(camera1[1]) + " and "
              + str(camera2[1]))

        cam = Camera(rtsp_link=camera1[0],
                     camera_id=camera1[1])
        cam2 = Camera(rtsp_link=camera2[0],
                     camera_id=camera2[1])

        subtraction_model = OD.SubtractionModel()
        subtraction_model2 = OD.SubtractionModel()

        while True:
            frame = cam.GetScaledNextFrame()
            frame2 = cam2.GetScaledNextFrame()

            subtraction_model2.FeedSubtractionModel(image=frame2, learningRate=0.0001)
            mask2 = subtraction_model2.GetOutput()

            cv2.imshow('camera1', frame)
            cv2.imshow('camera2', frame2)
            cv2.imshow('subtraction_model2', mask2)

            if cv2.waitKey(1) == 27:
                cam.release()
                cam2.release()
                cv2.destroyAllWindows()
                break
        # # Initialize camera
        # cam = Camera(rtsp_link=self.camera_rtsp,
        #              camera_id=self.camera_id)
        #
        # subtraction_model = OD.SubtractionModel()
        #
        # # Create shared memory space for frame and mask
        # frame = cam.GetScaledNextFrame()
        # subtraction_model.FeedSubtractionModel(image=frame, learningRate=0.0001)

        # self.detector_process = Process(target=self.Initialize, args=(camera1, camera2))
        # self.detector_process.start()