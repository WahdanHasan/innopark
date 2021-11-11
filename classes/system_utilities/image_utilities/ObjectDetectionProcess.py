import classes.system_utilities.image_utilities.ObjectDetection as OD
from classes.super_classes.ObjectTrackerListener import ObjectTrackerListener
from classes.system_utilities.helper_utilities.Enums import ShutDownEvent

from multiprocessing import Process

class DetectorProcess(ObjectTrackerListener):
    def __init__(self, amount_of_trackers, detector_request_queue, detector_initialized_event):
        ObjectTrackerListener.__init__(self, amount_of_trackers)

        self.detector_process = 0
        self.should_keep_listening = True

        self.detector_request_queue = detector_request_queue
        detector_initialized_event.set()

    def StartProcess(self):

        self.detector_process = Process(target=self.ListenForRequests)
        self.detector_process.start()

    def StopProcess(self):
        self.detector_process.terminate()

    def ListenForRequests(self):
        ObjectTrackerListener.initialize(self)

        OD.OnLoad()
        while self.should_keep_listening:
            instruction = self.detector_request_queue.get()

            if instruction == ShutDownEvent.SHUTDOWN:
                return

            (camera_id, requester_pipe) = instruction
            is_one_detection_above_threshold, class_names, bounding_boxes, confidence_scores = OD.DetectObjectsInImage(self.getFrameByCameraId(camera_id))

            requester_pipe.send((is_one_detection_above_threshold, class_names, bounding_boxes, confidence_scores))


