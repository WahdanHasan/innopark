from classes.camera.CameraBuffered import Camera
import classes.system_utilities.image_utilities.ObjectDetection as OD
import classes.system_utilities.image_utilities.ImageUtilities as IU
from classes.system_utilities.helper_utilities.Enums import DetectedObjectAtEntrance
from classes.system_utilities.tracking_utilities.ProcessLicenseFrames import ProcessLicenseFrames
import cv2
import numpy as np
from multiprocessing import Process, Pipe, shared_memory
from collections import deque
from shapely.geometry import Polygon, LineString


class EntranceLicenseDetector:
    def __init__(self):
        self.license_detector = 0
        self.shared_memory_manager_frames = 0
        #self.broker_request_queue = broker_request_queue
        self.bottom_camera = []
        self.top_camera = []
        self.should_keep_detecting_bottom_camera = False
        self.should_keep_detecting_top_camera = True
        self.maximum_bottom_camera_detection = 30
        self.latest_license_frames = deque([], maxlen=self.maximum_bottom_camera_detection)
        #self.latest_license_frames = np.zeros((30, 480, 720, 3))


    def InitializeCameras(self, bottom_camera, top_camera):
        # camera is given as type array in the format [camera rtsp, camera id]
        self.bottom_camera = bottom_camera
        self.top_camera = top_camera

    def StartProcess(self, bottom_camera, top_camera):
        print("[Entrance License] Starting license detector for cameras: " + str(bottom_camera[1]) + " and "
              + str(top_camera[1]))
        self.InitializeCameras(bottom_camera, top_camera)
        self.tracker_process = Process(target=self.StartDetecting())
        self.tracker_process.start()

    def StoreLicenseFrames(self, frame):
        self.latest_license_frames.append(frame)

    def StartDetecting(self):
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
        while True:
            totalFrames +=1
            frame_top = cam2.GetScaledNextFrame()

            frame_top = IU.DrawLine(frame_top, (width_left, 0), (width_left, height), thickness=2)
            frame_top = IU.DrawLine(frame_top, (width_right, 0), (width_right, height), thickness=2)

            cropped_frame_top = IU.CropImage(frame_top, [[width_left, 0], [width_right, height]])

            subtraction_model.FeedSubtractionModel(image=cropped_frame_top, learningRate=0.001)
            mask = subtraction_model.GetOutput()

            white_points_percentage = (np.sum(mask == 255)/(mask.shape[1]*mask.shape[0]))*100
            print(white_points_percentage)

            # totalFrame > 2 cuz the first mask starts at 100% white then it adapts
            if white_points_percentage >= 95 \
                    and old_detection_status != DetectedObjectAtEntrance.DETECTED_WITH_YOLO and totalFrames > 2:
                old_detection_status = DetectedObjectAtEntrance.DETECTED

                return_status, classes, bounding_boxes, _ = OD.DetectObjectsInImage(frame_top)

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
                        total_bottom_camera_count = 0
                        self.should_keep_detecting_bottom_camera = False

                        i = 0
                        for license_frame in self.latest_license_frames:
                            i+=1
                            cv2.imshow(str(i) +"/", license_frame)
                            cv2.waitKey(0)

            elif white_points_percentage < 95 and old_detection_status != DetectedObjectAtEntrance.NOT_DETECTED:
                old_detection_status = DetectedObjectAtEntrance.NOT_DETECTED

            # start capturing at most 30 license frames from bottom camera when car is detected with Yolo
            if self.should_keep_detecting_bottom_camera:
                print("hi")
                frame_bottom = cam.GetScaledNextFrame()
                self.StoreLicenseFrames(frame_bottom)
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