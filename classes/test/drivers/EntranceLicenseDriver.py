import cv2

from multiprocessing import Process, Queue, Event

def main():
    import classes.test.drivers.EntranceLicenseDriver as LD

    wait_license_processing_event = Event()

    license_frames_request_queue = Queue()

    license_detector_process = LD.StartEntranceLicenseDetector(license_frames_request_queue, wait_license_processing_event)
    license_processing_process = LD.StartProcessingLicenseFrames(license_frames_request_queue, wait_license_processing_event)

    cv2.namedWindow("Close this to close all license thingies")
    cv2.waitKey(0)

    license_detector_process.terminate()
    license_processing_process.terminate()

if __name__ == "__main__":
    main()


def StartEntranceLicenseDetector(license_frames_request_queue, wait_license_processing_event):
    from classes.system_utilities.tracking_utilities.EntranceLicenseDetector import EntranceLicenseDetector

    license_detector = EntranceLicenseDetector(license_frames_request_queue)
    license_detector.InitializeCameras(
        [0, "data\\reference footage\\test journey\\Entrance_Top.mp4"],
        [1, "data\\reference footage\\test journey\\Entrance_Bottom_Simulated_2.mp4"]
    )

    license_detector_process = Process(target=license_detector.Start, args=(wait_license_processing_event,))
    license_detector_process.start()

    return license_detector_process

def StartProcessingLicenseFrames(license_frames_request_queue, wait_license_processing_event):
    from classes.test.classes.Beta_ProcessLicenseFrames import ProcessLicenseFrames

    license_processing_frames = ProcessLicenseFrames(license_frames_request_queue)
    license_processing_process = Process(target=license_processing_frames.Start, args=(wait_license_processing_event,))
    license_processing_process.start()

    return license_processing_process

