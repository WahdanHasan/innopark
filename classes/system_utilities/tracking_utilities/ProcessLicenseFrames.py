import cv2
#from multiprocessing import Process
from classes.system_utilities.image_utilities import LicenseDetection
import numpy as np


class ProcessLicenseFrames:
    def __init__(self, license_frames_request_queue):
         self.license_frames_request_queue = license_frames_request_queue
         self.license_processing_process = 0

    def Start(self, event_wait_load):
        event_wait_load.set()

        # listen for voyager request
        latest_license_frames = self.license_frames_request_queue.get()

        license_plates = self.DetectLicensePlates(latest_license_frames)
        print("hi")

        # for plate in license_plates:
        #     cv2.imshow("plate", plate)
        #     cv2.waitKey(0)

    def StartProcess(self):
        self.license_processing_process = Process(target=self.Start)
        self.license_processing_process.start()

    def StopProcess(self):
        self.license_detector_process.terminate()

    def DetectLicensePlates(self, latest_license_frames):
        licenses = []

        cv2.imshow("license", latest_license_frames[0])
        cv2.waitKey(0)
        license_return_status, license_classes, \
        license_bounding_boxes, license_scores = LicenseDetection.DetectLicenseInImage(latest_license_frames[0])
        print(license_return_status)

        # for frame in latest_license_frames:
        #     dl = LicenseDetection.DetectLicenseInImage(frame)
        #     licenses.append(dl)

        return licenses



