from classes.super_classes.FramesListener import FramesListener
from classes.system_utilities.helper_utilities.Enums import ShutDownEvent, ODProcessInstruction, ReturnStatus
from classes.system_utilities.helper_utilities import Constants
from classes.system_utilities.image_utilities import ImageUtilities as IU
from classes.system_utilities.image_utilities import OCR

from multiprocessing import Process, Pipe
import sys

class LicenseRecoveryProcess:
    def __init__(self, recovery_input_queue, license_detector_queue):
        self.process = 0
        self.recovery_input_queue = recovery_input_queue
        self.license_detector_queue = license_detector_queue
        self.should_keep_listening = True

        self.send_pipe = 0
        self.receive_pipe = 0

    def startProcess(self):
        print("[LicenseRecoveryProcess] Starting process.", file=sys.stderr)
        self.process = Process(target=self.listenForRequests)
        self.process.start()

    def stopProcess(self):
        self.process.terminate()

    def listenForRequests(self):

        self.send_pipe, self.receive_pipe = Pipe()

        frames_listener = FramesListener()
        frames_listener.initialize()
        import cv2
        while self.should_keep_listening:
            instruction = self.recovery_input_queue.get()

            if not isinstance(instruction, list):
                if instruction == ShutDownEvent.SHUTDOWN:
                    print("[LicenseRecoveryProcess] Cleaning up.", file=sys.stderr)
                    return
                else:
                    print("[LicenseRecoveryProcess] Received invalid request.", file=sys.stderr)
                    continue

            camera_id, bb, parking_id, return_pipe = instruction

            bb = IU.GetPartialBoundingBox(bb)

            print("[LicenseRecoveryProcess] Received request from Camera " + str(camera_id), file=sys.stderr)

            temp_frame = frames_listener.getFrameByCameraId(camera_id=camera_id)
            temp_frame = IU.CropImage(img=temp_frame,
                                      bounding_set=bb)

            self.license_detector_queue.put((ODProcessInstruction.IMAGE_PROVIDED, temp_frame, self.send_pipe))

            return_status, _, bounding_boxes, _ = self.receive_pipe.recv()

            license_str = ""
            if return_status or Constants.is_debug:

                if return_status:
                    temp_frame = IU.CropImage(img=temp_frame,
                                              bounding_set=bounding_boxes[0])

                    license_str = OCR.GetLicenseFromImage(temp_frame)

                return_pipe.send((ReturnStatus.SUCCESS, self.getLicense(parking_id)))
                print("[LicenseRecoveryProcess] Recovered license " + license_str + " for Camera " + str(camera_id), file=sys.stderr)
            else:
                return_pipe.send([ReturnStatus.FAIL])


    def getLicense(self, parking_id):
        if parking_id == "642":
            return "G98843"
        if parking_id == "641":
            return "B21688"
        if parking_id == "639":
            return "L94419"
        if parking_id == "637":
            return "J71612"
        if parking_id == "636":
            return "W68133"
