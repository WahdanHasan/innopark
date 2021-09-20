import cv2
from classes.camera.CameraBuffered import Camera
from classes.system_utilities.tracking_utilities.EntranceLicenseDetector import EntranceLicenseDetector
from classes.system_utilities.tracking_utilities.ProcessLicenseFrames import ProcessLicenseFrames

from classes.system_utilities.image_utilities.ObjectDetection import DetectObjectsInImage
import multiprocessing

def main():

    import classes.test_drivers.EntranceLicenseDriver as LD
    license_frames_request_queue = multiprocessing.Queue()

    license_detector_process = LD.StartEntranceLicenseDetector(license_frames_request_queue)
    license_processing_process = LD.StartProcessingLicenseFrames(license_frames_request_queue)

    cv2.namedWindow("Close this to close all license thingies")
    cv2.waitKey(0)

    license_detector_process.terminate()
    license_processing_process.terminate()

if __name__ == "__main__":
    main()


def StartEntranceLicenseDetector(license_frames_request_queue):
    # license_detector = EntranceLicenseDetector()
    license_detector = EntranceLicenseDetector(license_frames_request_queue)
    # license_detector.StartProcess(["D:\\DownloadsD\\License_Footage\\Entrance_Bottom_Simulated_2.mp4", 0],
    #                              ["D:\\DownloadsD\\License_Footage\\Entrance_Top.mp4", 1])
    license_detector.InitializeCameras(
        ["D:\\ProgramData\\Grad Project\\Experiments\\License_Footage\\Entrance_Bottom_Simulated_2.mp4", 0],
        ["D:\\ProgramData\\Grad Project\\Experiments\\License_Footage\\Entrance_Top.mp4", 1]
    )
    # license_detector_process = multiprocessing.Process(target=license_detector.Start,
    #                                                    args=(license_frames_request_queue,))
    license_detector_process = multiprocessing.Process(target=license_detector.Start)
    license_detector_process.start()

    return license_detector_process

def StartProcessingLicenseFrames(license_frames_request_queue):
    license_processing_frames = ProcessLicenseFrames(license_frames_request_queue)
    # license_processing_process = multiprocessing.Process(target=license_processing_frames.Start,
    #                                                      args=(license_frames_request_queue,))
    license_processing_process = multiprocessing.Process(target=license_processing_frames.Start)
    license_processing_process.start()

    return license_processing_process

