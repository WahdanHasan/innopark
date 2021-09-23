import cv2
# from multiprocessing import Process
from classes.system_utilities.image_utilities import LicenseDetection
import time
import numpy as np
import classes.system_utilities.image_utilities.ImageUtilities as IU


class ProcessLicenseFrames:
    def __init__(self, license_frames_request_queue):
        self.license_frames_request_queue = license_frames_request_queue
        self.license_processing_process = 0

    def Start(self, wait_license_processing_event):
        wait_license_processing_event.set()

        while True:
            print("listening to queue for incoming license frames")
            # listen for voyager request
            latest_license_frames = self.license_frames_request_queue.get()

            # detect license plates from frames
            license_plates = self.DetectLicensePlates(latest_license_frames)
            print("exited the point of no return")

            # extract info from license plates
            license_plates_info = self.ExtractLicensePlatesInfo(license_plates)

            # determine the license plate of the vehicle
            license = self.GetProminentLicensePlate(license_plates_info)

            # send the license to broker


            if cv2.waitKey(1) == 27:
                cv2.destroyAllWindows()
                break

    def StartProcess(self):
        self.license_processing_process = Process(target=self.Start)
        self.license_processing_process.start()

    def StopProcess(self):
        self.license_detector_process.terminate()

    def DetectLicensePlates(self, latest_license_frames):
        # extracts license plates from frames
        # gets a list of frames that potentially contain license plates
        # returns a list license plates detected

        license_plates = []

        print("entering the point of no return")
        time.sleep(40)

        for i in range(len(latest_license_frames)):
            # detect the license plate in frame and get its bbox coordinates
            license_return_status, license_classes, \
            license_bounding_boxes, _ = LicenseDetection.DetectLicenseInImage(latest_license_frames[i])

            # crop the frame using bbox if a license is found in frame
            if license_return_status:
                license_bounding_boxes_converted = [[license_bounding_boxes[0][0][0], license_bounding_boxes[0][0][1]],
                                                    [license_bounding_boxes[0][1][0], license_bounding_boxes[0][1][1]]]
                plate = IU.CropImage(latest_license_frames[i], license_bounding_boxes_converted)

                # add the cropped frame containing only the license to the list of licenses
                license_plates.append(plate)

        return license_plates

    def ExtractLicensePlatesInfo(self, license_plates):
        # extract license plate info using OCR
        # gets a list of license plates
        # returns a list of the license plate info

        license_plates_info = []

        for plate in license_plates:
            plate_info = LicenseDetection.GetLicenseFromImage(plate)
            license_plates_info.append(plate_info)

        return license_plates_info

    def GetProminentLicensePlate(self, license_plates_info):
        # find the license plate that appears the most
        # gets a list of the license plate info
        # return a single license plate, the most prominent one

        prominent_license_plate = license_plates_info[0]
        licenses = {}

        for license_info in license_plates_info:
            key = license_info
            found = False

            for license in licenses:
                if license_info == license:
                    licenses[key] += 1
                    found = True
                    break

            if not found:
                licenses[key] = 1

        print("licenses: ", licenses)

        for key in licenses:
            if licenses[key] > licenses[prominent_license_plate]:
                prominent_license_plate = key

        print("the chosen: ", prominent_license_plate)

        return prominent_license_plate
