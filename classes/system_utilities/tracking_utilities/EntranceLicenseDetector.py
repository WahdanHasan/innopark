import classes.system_utilities.image_utilities.ObjectDetection as OD
from classes.system_utilities.tracking_utilities.SubtractionModel import SubtractionModel
import classes.system_utilities.image_utilities.ImageUtilities as IU
import cv2
import numpy as np
from classes.camera.CameraBuffered import Camera
from multiprocessing import Process
from classes.system_utilities.helper_utilities.Enums import DetectedObjectAtEntrance
from classes.system_utilities.helper_utilities import Constants
from shapely.geometry import Polygon, LineString


class EntranceLicenseDetector:
    def __init__(self, license_frames_request_queue, broker_request_queue, top_camera, bottom_camera, wait_license_processing_event):
        # camera is given as type array in the format [camera id, camera rtsp]

        self.license_frames_request_queue = license_frames_request_queue
        self.license_detector_process = 0
        self.license_processing_process = 0
        self.broker_request_queue = broker_request_queue
        self.wait_license_processing_event = wait_license_processing_event

        self.bottom_camera = bottom_camera
        self.top_camera = top_camera

        self.should_keep_detecting_bottom_camera = False
        self.should_keep_detecting_top_camera = True
        self.maximum_bottom_camera_detection = 1
        self.latest_license_frames = np.zeros((self.maximum_bottom_camera_detection, 480, 720, 3), dtype='uint8')

    def StartProcess(self):
        self.license_detector_process = Process(target=self.Start)
        self.license_detector_process.start()

        from classes.system_utilities.tracking_utilities.ProcessLicenseFrames import ProcessLicenseFrames
        temp_process_license_frames = ProcessLicenseFrames(broker_request_queue=self.broker_request_queue,
                                                           license_frames_request_queue=self.license_frames_request_queue,
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

        OD.DetectObjectsInImage(np.zeros((Constants.default_camera_shape[1], Constants.default_camera_shape[1], 3), dtype='uint8'))


        bottom_camera = Camera(rtsp_link=self.bottom_camera[1],
                               camera_id=self.bottom_camera[0])
        top_camera = Camera(rtsp_link=self.top_camera[1],
                            camera_id=self.top_camera[0])

        subtraction_model = SubtractionModel()
        frame_top = top_camera.GetScaledNextFrame()

        (height, width) = frame_top.shape[:2]
        width_median = width/2
        width_left = int(width_median - (width_median*0.1))
        width_right = int(width_median + (width_median*0.1))

        old_detection_status = DetectedObjectAtEntrance.NOT_DETECTED

        total_bottom_camera_count = 0
        white_points_threshold = 95

        self.wait_license_processing_event.wait()

        while self.should_keep_detecting_top_camera:
            frame_top = top_camera.GetScaledNextFrame()
            frame_bottom = bottom_camera.GetScaledNextFrame()

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

                return_status, classes, bounding_boxes, _ = OD.DetectObjectsInImage(frame_top)

                # if vehicle is detected, start capturing frames (max of self.maximum_bottom_camera_detection)
                # until the vehicle's bb intersects with the frame median block
                # once vehicle's bb intersects, send the captured frames to another process
                if return_status:
                    frame_top = IU.DrawBoundingBoxes(frame_top, bounding_boxes)

                    polygon_bbox = Polygon([(bounding_boxes[0][0][0], bounding_boxes[0][0][1]),
                                            (bounding_boxes[0][1][0], bounding_boxes[0][0][1]),
                                            (bounding_boxes[0][1][0], bounding_boxes[0][1][1]),
                                            (bounding_boxes[0][0][0], bounding_boxes[0][1][1])])
                    line_median_right = LineString([(width_right, 0), (width_right, height)])
                    intersection = line_median_right.intersects(polygon_bbox)

                    self.should_keep_detecting_bottom_camera = True

                    if intersection:
                        print("INTERSECTION: ", intersection)
                        old_detection_status = DetectedObjectAtEntrance.DETECTED_WITH_YOLO

                        # send the frames to another process be processed
                        self.license_frames_request_queue.put(self.latest_license_frames)

            # if the white percentage is below threshold, stop detection
            elif white_points_percentage < white_points_threshold and old_detection_status != DetectedObjectAtEntrance.NOT_DETECTED:
                old_detection_status = DetectedObjectAtEntrance.NOT_DETECTED

            cv2.imshow('bottom_camera', frame_top)
            cv2.imshow('subtraction_model', mask)

            if cv2.waitKey(1) == 27:
                bottom_camera.ReleaseFeed()
                top_camera.ReleaseFeed()
                cv2.destroyAllWindows()
                break