import cv2
from multiprocessing import Process
from classes.system_utilities.helper_utilities.Enums import TrackedObjectToBrokerInstruction, EntrantSide

import classes.system_utilities.image_utilities.ImageUtilities as IU


class ProcessLicenseFrames:
    def __init__(self, broker_request_queue, license_frames_request_queue, camera_id, wait_license_processing_event):
        self.license_frames_request_queue = license_frames_request_queue
        self.wait_license_processing_event = wait_license_processing_event
        self.license_processing_process = 0
        self.broker_request_queue = broker_request_queue
        self.camera_id = camera_id

    def Start(self):
        from classes.system_utilities.image_utilities import LicenseDetection
        LicenseDetection.OnLoad()

        self.wait_license_processing_event.set()
        while True:
            # listen for voyager request
            latest_license_frames = self.license_frames_request_queue.get()

            # detect license plates from frames
            license_plates = self.DetectLicensePlates(latest_license_frames=latest_license_frames,
                                                      license_detector=LicenseDetection)

            # extract info from license plates
            license_plates_info = self.ExtractLicensePlatesInfo(license_plates=license_plates,
                                                                LicenseDetection=LicenseDetection)

            # determine the license plate of the vehicle
            detected_license = self.GetProminentLicensePlate(license_plates_info)

            # send the license to broker
            self.broker_request_queue.put((TrackedObjectToBrokerInstruction.PUT_VOYAGER, self.camera_id, detected_license, EntrantSide.LEFT))

            if cv2.waitKey(1) == 27:
                cv2.destroyAllWindows()
                break

    def StartProcess(self):
        self.license_processing_process = Process(target=self.Start)
        self.license_processing_process.start()

        return self.license_processing_process

    def StopProcess(self):
        self.license_detector_process.terminate()

    def DetectLicensePlates(self, latest_license_frames, license_detector):
        # extracts license plates from frames
        # gets a list of frames that potentially contain license plates
        # returns a list license plates detected

        license_plates = []

        for i in range(len(latest_license_frames)):
            # detect the license plate in frame and get its bbox coordinates
            license_return_status, license_classes, license_bounding_boxes, _ = license_detector.DetectLicenseInImage(image=latest_license_frames[i])

            # crop the frame using bbox if a license is found in frame
            if license_return_status:
                license_bounding_boxes_converted = license_bounding_boxes[0]
                plate = IU.CropImage(latest_license_frames[i], license_bounding_boxes_converted)

                # add the cropped frame containing only the license to the list of licenses
                license_plates.append(plate)

        return license_plates

    def ExtractLicensePlatesInfo(self, license_plates, LicenseDetection):
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
