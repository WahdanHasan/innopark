import classes.system_utilities.image_utilities.ObjectDetection as OD
from classes.system.super_classes.TrackedObjectListener import TrackedObjectListener
from multiprocessing import Process
import sys

class DetectorProcess(TrackedObjectListener):
    def __init__(self, amount_of_trackers, base_pool_size, new_object_in_pool_event, detector_request_queue, detector_initialized_event):
        super().__init__(amount_of_trackers, base_pool_size, new_object_in_pool_event)

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
        self.Initialize()

        while self.should_keep_listening:
            (tracker_id, requester_pipe) = self.detector_request_queue.get()

            print("[ObjectDetectionProcess] Received request from Tracker " + str(tracker_id), file=sys.stderr)
            requester_pipe.send((OD.DetectObjectsInImage(self.GetTrackerFrameByTrackerId(tracker_id))))

