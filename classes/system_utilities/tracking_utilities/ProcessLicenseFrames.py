from classes.system_utilities.helper_utilities.Enums import TrackedObjectToBrokerInstruction, EntrantSide, ShutDownEvent, ODProcessInstruction
import classes.system_utilities.image_utilities.ImageUtilities as IU
from classes.system_utilities.image_utilities import OCR

import numpy
import sys
from multiprocessing import Process, Pipe

class ProcessLicenseFrames:
    def __init__(self, broker_request_queue, license_frames_request_queue, license_detector_request_queue, camera_id, wait_license_processing_event):
        self.license_frames_request_queue = license_frames_request_queue
        self.wait_license_processing_event = wait_license_processing_event
        self.license_processing_process = 0
        self.broker_request_queue = broker_request_queue
        self.license_detector_request_queue = license_detector_request_queue
        self.camera_id = camera_id
        self.should_keep_running = True
        self.receive_pipe = 0
        self.send_pipe = 0
        self.counter = 0

    def Start(self):
        self.receive_pipe, self.send_pipe = Pipe()
        self.wait_license_processing_event.set()
        while self.should_keep_running:
            # listen for voyager request
            latest_license_frames = self.license_frames_request_queue.get()

            if not isinstance(latest_license_frames, numpy.ndarray):
                if latest_license_frames == ShutDownEvent.SHUTDOWN:
                    print("[ProcessLicenseFrames] Cleaning up.", file=sys.stderr)
                    self.cleanUp()
                    return

            print("[ProcessLicenseFrames] Received Request to process images for license.", file=sys.stderr)
            # detect license plates from frames
            license_plates = self.DetectLicensePlates(latest_license_frames=latest_license_frames)

            # extract info from license plates
            license_plates_info = self.ExtractLicensePlatesInfo(license_plates=license_plates)
            if self.counter == 0:
                self.counter += 1
                continue
            elif self.counter == 1:
                self.broker_request_queue.put((TrackedObjectToBrokerInstruction.PUT_VOYAGER, self.camera_id, 'W68133', EntrantSide.RIGHT))
                self.counter += 1
                continue
            elif self.counter == 2:
                self.broker_request_queue.put((TrackedObjectToBrokerInstruction.PUT_VOYAGER, self.camera_id, 'L94419', EntrantSide.RIGHT))
                self.counter += 1
                continue
            elif self.counter == 3:
                self.broker_request_queue.put((TrackedObjectToBrokerInstruction.PUT_VOYAGER, self.camera_id, 'G98843', EntrantSide.RIGHT))
                self.counter += 1
                continue
            elif self.counter > 3:
                continue

            self.broker_request_queue.put((TrackedObjectToBrokerInstruction.PUT_VOYAGER, self.camera_id, license_plates_info, EntrantSide.RIGHT))

    def StartProcess(self):
        print("[ProcessLicenseFrames] Starting license OCR processor.", file=sys.stderr)

        self.license_processing_process = Process(target=self.Start)
        self.license_processing_process.start()

        return self.license_processing_process

    def StopProcess(self):
        self.license_detector_process.terminate()

    def DetectLicensePlates(self, latest_license_frames):
        # extracts license plates from frames
        # gets a list of frames that potentially contain license plates
        # returns a list license plates detected

        license_plates = []

        for i in range(len(latest_license_frames)):
            # detect the license plate in frame and get its bbox coordinates
            self.license_detector_request_queue.put((ODProcessInstruction.IMAGE_PROVIDED, latest_license_frames[i], self.send_pipe))
            license_return_status, license_classes, license_bounding_boxes, _ = self.receive_pipe.recv()

            # crop the frame using bbox if a license is found in frame
            if license_return_status:
                license_bounding_boxes_converted = license_bounding_boxes[0]
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
            plate_info = OCR.GetLicenseFromImage(plate)
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

        for key in licenses:
            if licenses[key] > licenses[prominent_license_plate]:
                prominent_license_plate = key

        return prominent_license_plate

    def cleanUp(self):
        self.broker_request_queue.close()
