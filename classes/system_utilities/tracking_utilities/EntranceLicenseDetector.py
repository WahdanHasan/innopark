from classes.camera.CameraBuffered import Camera
from classes.system_utilities.tracking_utilities.SubtractionModel import SubtractionModel
from classes.super_classes.ShutDownEventListener import ShutDownEventListener
import classes.system_utilities.image_utilities.ImageUtilities as IU
from classes.system_utilities.helper_utilities.Enums import DetectedObjectAtEntrance, ODProcessInstruction
from classes.system_utilities.helper_utilities import Constants
from classes.system_utilities.helper_utilities.Enums import ShutDownEvent

import numpy as np
import sys
import time
from multiprocessing import Process, shared_memory, Pipe
from shapely.geometry import Polygon, LineString


class EntranceLicenseDetector(ShutDownEventListener):
    def __init__(self, license_frames_request_queue, broker_request_queue, detector_request_queue, license_detector_request_queue, top_camera, bottom_camera, entrance_cameras_initialized_event, wait_license_processing_event, shutdown_event, start_system_event, seconds_between_detections=1):
        ShutDownEventListener.__init__(self, shutdown_event)
        # camera is given as type array in the format [camera id, camera rtsp]

        self.license_frames_request_queue = license_frames_request_queue
        self.license_detector_process = 0
        self.license_processing_process = 0
        self.broker_request_queue = broker_request_queue
        self.wait_license_processing_event = wait_license_processing_event
        self.entrance_cameras_initialized_event = entrance_cameras_initialized_event
        self.shutdown_event = shutdown_event
        self.start_system_event = start_system_event
        self.seconds_between_detections = seconds_between_detections
        self.detector_request_queue = detector_request_queue
        self.license_detector_request_queue = license_detector_request_queue

        self.bottom_camera = bottom_camera
        self.top_camera = top_camera

        self.shared_memory_manager_frame_top = 0
        self.shared_memory_manager_frame_bottom = 0
        self.should_keep_detecting_bottom_camera = False
        self.should_keep_detecting_top_camera = True
        self.maximum_bottom_camera_detection = 1
        self.latest_license_frames = np.zeros((self.maximum_bottom_camera_detection, 480, 720, 3), dtype='uint8')

    def StartProcess(self):
        print("[EntranceLicenseDetector] Starting license detector.", file=sys.stderr)
        self.license_detector_process = Process(target=self.Start)
        self.license_detector_process.start()
        
        from classes.system_utilities.tracking_utilities.ProcessLicenseFrames import ProcessLicenseFrames
        temp_process_license_frames = ProcessLicenseFrames(broker_request_queue=self.broker_request_queue,
                                                           license_frames_request_queue=self.license_frames_request_queue,
                                                           license_detector_request_queue=self.license_detector_request_queue,
                                                           camera_id=self.bottom_camera[0],
                                                           wait_license_processing_event=self.wait_license_processing_event)

        self.license_processing_process = temp_process_license_frames.StartProcess()

        return self.license_detector_process

    def StopProcess(self):
        self.license_detector_process.terminate()
        self.license_processing_process.terminate()

    def StoreLicenseCameraFrame(self, frame, index):
        self.latest_license_frames[index] = frame

    def Start(self):

        receive_pipe, send_pipe = Pipe()

        ShutDownEventListener.initialize(self)

        bottom_camera = Camera(rtsp_link=self.bottom_camera[1],
                               camera_id=self.bottom_camera[0])
        top_camera = Camera(rtsp_link=self.top_camera[1],
                            camera_id=self.top_camera[0])

        subtraction_model = SubtractionModel()
        frame_top = top_camera.GetScaledNextFrame()
        frame_bottom = bottom_camera.GetScaledNextFrame()

        (height, width) = frame_top.shape[:2]
        width_median = width/2
        width_left = int(width_median - (width_median*0.1))
        width_right = int(width_median + (width_median*0.1))

        old_detection_status = DetectedObjectAtEntrance.NOT_DETECTED

        total_bottom_camera_count = 0
        white_points_threshold = 95

        self.shared_memory_manager_frame_top = shared_memory.SharedMemory(create=True,
                                                                          name=Constants.frame_shared_memory_prefix + str(self.top_camera[0]),
                                                                          size=frame_top.nbytes)

        self.shared_memory_manager_frame_bottom = shared_memory.SharedMemory(create=True,
                                                                             name=Constants.frame_shared_memory_prefix + str(self.bottom_camera[0]),
                                                                             size=frame_bottom.nbytes)

        self.entrance_cameras_initialized_event.set()

        frame_top_sm = np.ndarray(frame_top.shape, dtype=np.uint8, buffer=self.shared_memory_manager_frame_top.buf)
        frame_bottom_sm = np.ndarray(frame_bottom.shape, dtype=np.uint8, buffer=self.shared_memory_manager_frame_bottom.buf)

        time_at_detection = time.time()

        self.wait_license_processing_event.wait()
        self.start_system_event.wait()

        while self.should_keep_detecting_top_camera:
            if not self.shutdown_should_keep_listening:
                print("[EntranceLicenseDetector] Cleaning up.", file=sys.stderr)
                self.license_frames_request_queue.put(ShutDownEvent.SHUTDOWN)
                self.cleanUp()
                return

            frame_top_sm[:] = top_camera.GetScaledNextFrame()[:]
            frame_bottom_sm[:] = bottom_camera.GetScaledNextFrame()[:]

            frame_top = frame_top_sm.copy()
            frame_bottom = frame_bottom_sm.copy()

            # Store the latest bottom camera frame
            if total_bottom_camera_count == self.maximum_bottom_camera_detection:
                total_bottom_camera_count = 0

            self.StoreLicenseCameraFrame(frame_bottom, total_bottom_camera_count)
            total_bottom_camera_count += 1

            # get the frame median
            cropped_frame_top = IU.CropImage(frame_top, [[width_left, 0], [width_right, height]])

            # draw the frame median block
            frame_top = IU.DrawLine(frame_top, (width_left, 0), (width_left, height), thickness=2)
            frame_top = IU.DrawLine(frame_top, (width_right, 0), (width_right, height), thickness=2)

            # apply the subtraction model on the frame median block
            subtraction_model.FeedSubtractionModel(image=cropped_frame_top, learningRate=0.001)
            mask = subtraction_model.GetOutput()

            # calculate the white percentage in the subtraction model mask to detect a potential new vehicle
            white_points_percentage = (np.sum(mask == 255)/(mask.shape[1]*mask.shape[0]))*100

            # if the white percentage is above the threshold specified, run Yolo to detect vehicle
            if white_points_percentage >= white_points_threshold and old_detection_status != DetectedObjectAtEntrance.DETECTED_WITH_YOLO:
                old_detection_status = DetectedObjectAtEntrance.DETECTED

                if (time.time() - time_at_detection) > self.seconds_between_detections:
                    self.detector_request_queue.put((ODProcessInstruction.IMAGE_PROVIDED, frame_top, send_pipe))
                    return_status, classes, bounding_boxes, _ = receive_pipe.recv()
                    time_at_detection = time.time()
                else:
                    return_status = False
                    old_detection_status = DetectedObjectAtEntrance.NOT_DETECTED
                    self.should_keep_detecting_bottom_camera = True

                # if vehicle is detected, start capturing frames (max of self.maximum_bottom_camera_detection)
                # until the vehicle's bb intersects with the frame median block
                # once vehicle's bb intersects, send the captured frames to another process
                if return_status:
                    bounding_boxes = bounding_boxes[0]
                    bounding_boxes = IU.GetFullBoundingBox(bounding_boxes)
                    polygon_bbox = Polygon(bounding_boxes)
                    line_median_right = LineString([(width_right, 0), (width_right, height)])
                    intersection = line_median_right.intersects(polygon_bbox)
                    self.should_keep_detecting_bottom_camera = True
                    if intersection:
                        old_detection_status = DetectedObjectAtEntrance.DETECTED_WITH_YOLO

                        print("[EntranceLicenseDetector] Detected Vehicle.", file=sys.stderr)

                        # send the frames to another process be processed
                        self.license_frames_request_queue.put(self.latest_license_frames)

            # if the white percentage is below threshold, stop detection
            elif white_points_percentage < white_points_threshold and old_detection_status != DetectedObjectAtEntrance.NOT_DETECTED:
                old_detection_status = DetectedObjectAtEntrance.NOT_DETECTED

    def cleanUp(self):
        self.shared_memory_manager_frame_top.unlink()
        self.shared_memory_manager_frame_bottom.unlink()
        time.sleep(1)
