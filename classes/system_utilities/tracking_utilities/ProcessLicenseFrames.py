import cv2


class ProcessLicenseFrames:
    def __init__(self, license_frames_request_queue):
         self.license_frames_request_queue = license_frames_request_queue

    def Start(self):
        # listen for voyager request
        latest_license_frames = self.license_frames_request_queue.get()

        license_plate = self.GetLicensePlate(latest_license_frames)

    def GetLicensePlate(self, latest_license_frames):

        unique_plates = []
        # for plate in (latest_license_frames):
        #     cv2.imshow("plate", plate)
        #     cv2.waitKey(0)

        return 1



