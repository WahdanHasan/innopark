import classes.system_utilities.image_utilities.ObjectDetection as OD
import classes.system_utilities.image_utilities.ImageUtilities as IU
import cv2
import numpy as np
from classes.camera.CameraBuffered import Camera
from multiprocessing import Process, Pipe, shared_memory
from classes.system_utilities.helper_utilities.Enums import DetectedObjectAtEntrance
from collections import deque
from shapely.geometry import Polygon, LineString


class EntranceLicenseDetector:
    def __init__(self, license_frames_request_queue):
        self.license_frames_request_queue = license_frames_request_queue
        self.license_detector_process = 0

        self.bottom_camera = []
        self.top_camera = []

        self.should_keep_detecting_bottom_camera = False
        self.should_keep_detecting_top_camera = True
        self.maximum_bottom_camera_detection = 30
        self.latest_license_frames = np.zeros((self.maximum_bottom_camera_detection, 480, 720, 3), dtype='uint8')

    def InitializeCameras(self, bottom_camera, top_camera):
        # camera is given as type array in the format [camera rtsp, camera id]
        self.bottom_camera = bottom_camera
        self.top_camera = top_camera

    def StartProcess(self, bottom_camera, top_camera):
        print("[Entrance License] Starting license detector for cameras: " + str(bottom_camera[1]) + " and "
              + str(top_camera[1]))
        self.InitializeCameras(bottom_camera, top_camera)
        self.license_detector_process = Process(target=self.Start)
        self.license_detector_process.start()

    def StopProcess(self):
        self.license_detector_process.terminate()

    def StoreLicenseFrames(self, frame, index):
        self.latest_license_frames[index] = frame

    def Start(self):
        cam = Camera(rtsp_link=self.bottom_camera[0],
                     camera_id=self.bottom_camera[1])
        cam2 = Camera(rtsp_link=self.top_camera[0],
                      camera_id=self.top_camera[1])

        subtraction_model = OD.SubtractionModel()
        frame_top = cam2.GetScaledNextFrame()

        (height, width) = frame_top.shape[:2]
        width_median = width/2
        width_left = int(width_median - (width_median*0.1))
        width_right = int(width_median + (width_median*0.1))

        old_detection_status = DetectedObjectAtEntrance.NOT_DETECTED

        totalFrames = 1
        total_bottom_camera_count = 0
        white_points_threshold = 95
        while True:
            totalFrames +=1
            frame_top = cam2.GetScaledNextFrame()

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

            # totalFrame > 2 cuz the first mask starts at 100% white then it adapts
            # if the white percentage is above the threshold specified, run Yolo to detect vehicle
            if white_points_percentage >= white_points_threshold \
                    and old_detection_status != DetectedObjectAtEntrance.DETECTED_WITH_YOLO and totalFrames > 2:
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
                    print("INTERSECTION: ", intersection)

                    self.should_keep_detecting_bottom_camera = True

                    if intersection:
                        old_detection_status = DetectedObjectAtEntrance.DETECTED_WITH_YOLO
                        self.should_keep_detecting_bottom_camera = False
                        total_bottom_camera_count = 0

                        # send the frames to another process be processed
                        self.license_frames_request_queue.put(self.latest_license_frames)

            # if the white percentage is below threshold, stop detection
            elif white_points_percentage < white_points_threshold and old_detection_status != DetectedObjectAtEntrance.NOT_DETECTED:
                old_detection_status = DetectedObjectAtEntrance.NOT_DETECTED

            # once vehicle is detected using Yolo, start capturing frames
            if self.should_keep_detecting_bottom_camera:
                # added as a pre-caution if car doesn't intersect with median in a second
                if total_bottom_camera_count > 30:
                    print("total bottom camera count is reset to 0")
                    total_bottom_camera_count = 0

                frame_bottom = cam.GetScaledNextFrame()

                self.StoreLicenseFrames(frame_bottom, total_bottom_camera_count)
                total_bottom_camera_count += 1

            cv2.imshow('bottom_camera', frame_top)
            cv2.imshow('subtraction_model', mask)

            if cv2.waitKey(1) == 27:
                cam.release()
                cam2.release()
                cv2.destroyAllWindows()
                break

# left_side_bbox = LineString([(bounding_boxes[0][0][0], bounding_boxes[0][0][1]),
#                              (bounding_boxes[0][0][0], bounding_boxes[0][1][1])])