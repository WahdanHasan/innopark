import classes.system_utilities.image_utilities.ObjectDetection as OD
from classes.super_classes.ObjectTrackerListener import ObjectTrackerListener
from multiprocessing import Process
import time

class DetectorProcess(ObjectTrackerListener):
    def __init__(self, amount_of_trackers, detector_request_queue, detector_initialized_event,  shutdown_event):
        super().__init__(amount_of_trackers)

        self.detector_process = 0
        self.should_keep_listening = True

        self.shutdown_event = shutdown_event
        self.detector_request_queue = detector_request_queue
        detector_initialized_event.set()

    def StartProcess(self):

        self.detector_process = Process(target=self.ListenForRequests)
        self.detector_process.start()

    def StopProcess(self):
        self.detector_process.terminate()

    def ListenForRequests(self):
        self.initialize()
        OD.OnLoad()
        while self.should_keep_listening:
            (camera_id, requester_pipe) = self.detector_request_queue.get()
            start_time = time.time()
            is_one_detection_above_threshold, class_names, bounding_boxes, confidence_scores = OD.DetectObjectsInImage(self.getFrameByCameraId(camera_id))
            # print("[CAMERA "+str(camera_id)+"]" + str(time.time() - start_time))
            requester_pipe.send((is_one_detection_above_threshold, class_names, bounding_boxes, confidence_scores))
            # break

