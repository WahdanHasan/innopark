import classes.system_utilities.image_utilities.ObjectDetection as OD
import classes.system_utilities.image_utilities.ImageUtilities as IU
import cv2
import time
import numpy as np
from multiprocessing import Process, Pipe
from classes.camera.CameraBuffered import Camera
import ctypes
from classes.enum_classes.Enums import ObjectStatus

class ParkingSpace:
    def __init__(self):
        self.id = -1
        self.bb = []
        self.is_occupied = False

    def UpdateId(self, new_id):
        self.id = new_id

    def UpdateBB(self, new_bb):
        # [TL, TR, BL, BR]
        self.bb = new_bb

    def UpdateStatus(self, is_occupied):
        self.is_occupied = is_occupied


class TrackedObject:
    def __init__(self, object_id, bb):
        self.object_id = object_id
        self.bb = bb

    def StartTracking(self, pipe):

        while True:

            [frame, mask] = pipe.recv()
            # cv2.imshow("me smoll process frame ", frame)
            # OD.CreateInvertedMask(frame, self.bb)

            # pipe.send(self.bb)
            # cv2.imshow("frame", frame)
            # cv2.imshow("mask", mask)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break




class Tracker:
    import time
    def __init__(self, is_debug_mode):

        self.tracker_process = 0
        self.parking_spaces = []
        self.is_debug_mode = is_debug_mode

    def Start(self, camera_rtsp, camera_id):
        # All parking spots should be instantiated prior to calling this function

        # ADD MASK INITIALIZATION HERE !!!!!!!!!
        self.tracker_process = Process(target=self.Update, args=(camera_rtsp, camera_id))
        self.tracker_process.start()

    def Stop(self):
        # Sets the tracker continue to false then waits for it to stop
        self.tracker_process.terminate()

    # def Update(self, camera_rtsp, camera_id):
    #
    #     parking_space_boxes = []
    #
    #     for i in range(len(self.parking_spaces)):
    #         parking_space_boxes.append(self.parking_spaces[i].bb)
    #
    #     cam_parking = Camera(rtsp_link=camera_rtsp,
    #                          camera_id=camera_id)
    #
    #     start_time = time.time()
    #     seconds_before_display = 1  # displays the frame rate every 1 second
    #     counter = 0
    #
    #     while True:
    #
    #         frame_parking = cam_parking.GetScaledNextFrame()
    #
    #         parking_return_status, parking_classes, parking_bounding_boxes, parking_scores = OD.DetectObjectsInImage(frame_parking)
    #
    #         # if parking_return_status == True:
    #         frame_yolo = IU.DrawBoundingBoxAndClasses(image=frame_parking,
    #                                                   class_names=parking_classes,
    #                                                   probabilities=parking_scores,
    #                                                   bounding_boxes=parking_bounding_boxes)
    #
    #
    #         parking_space_occupied_statuses = []
    #         if len(parking_space_boxes) != 0:
    #             for i in range(len(self.parking_spaces)):
    #                 parking_space_occupied_statuses.append(self.parking_spaces[i].is_occupied)
    #
    #             frame_yolo = IU.DrawParkingBoxes(frame_yolo, parking_space_boxes, parking_space_occupied_statuses)
    #
    #         for i in range(len(self.parking_spaces)):
    #             for j in range(len(parking_bounding_boxes)):
    #                 if OD.IsCarInParkingBBN(self.parking_spaces[i].bb, parking_bounding_boxes[j]):
    #                     cv2.imshow("MASK", OD.CreateInvertedMask(frame_parking, parking_bounding_boxes[j]))
    #                     self.parking_spaces[i].is_occupied = True
    #                 else:
    #                     self.parking_spaces[i].is_occupied = False
    #
    #
    #
    #         cv2.imshow("Camera " + str(camera_id) + " YOLO Detection", frame_yolo)
    #
    #         cv2.imshow("Camera " + str(camera_id) + " view", frame_parking)
    #
    #         counter += 1
    #         if (time.time() - start_time) > seconds_before_display:
    #             print("Camera " + str(camera_id) + " FPS: ", counter / (time.time() - start_time))
    #             counter = 0
    #             start_time = time.time()
    #
    #         if cv2.waitKey(1) & 0xFF == ord('q'):
    #             cv2.destroyAllWindows()
    #             break

    def Update(self, camera_rtsp, camera_id):

        old_tracked_boxes = []
        new_tracked_boxes = []

        old_ids = []

        # Initialize camera
        cam = Camera(rtsp_link=camera_rtsp,
                     camera_id=camera_id)


        height, width = cam.default_resolution[1], cam.default_resolution[0]

        self.base_mask = np.zeros((height, width, 3), dtype='uint8')

        # Debug variables
        start_time = time.time()
        seconds_before_display = 1
        counter = 0

        subtraction_model = OD.SubtractionModel()

        id_ctr = 0

        # Main loop
        while True:

            frame = cam.GetScaledNextFrame()

            subtraction_model.FeedSubtractionModel(frame, 0.0001)

            # Detect new entrants
            return_status, detected_ids, detected_bbs = self.DetectNewEntrants(frame)

            old_box_centers = []
            new_box_centers = []

            for i in range(len(old_tracked_boxes)):
                old_box_centers.append(IU.GetBoundingBoxCenter(old_tracked_boxes[i]))

            for i in range(len(detected_bbs)):
                new_box_centers.append(IU.GetBoundingBoxCenter(detected_bbs[i]))

            for i in range(len(detected_bbs)):
                for j in range(len(old_tracked_boxes)):
                    a = np.array(detected_bbs[i])
                    b = np.array(old_tracked_boxes[j])
                    if np.linalg.norm(abs(a - b)) < 10:
                        print("YES")



            old_tracked_boxes = detected_bbs

            frame_processed = IU.DrawBoundingBoxes(image=frame,
                                                   bounding_boxes=detected_bbs,
                                                   thickness=2)

            return_status, classes, bounding_boxes = self.DetectNewEntrants(frame)

            if return_status:
                for i in range(len(classes)):
                    temp_id =10


            # Information code
            if self.is_debug_mode:
                counter += 1
                if (time.time() - start_time) > seconds_before_display:
                    print("Camera " + str(camera_id) + " FPS: ", counter / (time.time() - start_time))
                    counter = 0
                    start_time = time.time()

                cv2.imshow("Camera " + str(camera_id) + " Live Feed", frame)
                cv2.imshow("Camera " + str(camera_id) + " Processed Feed", frame_processed)
                cv2.imshow("Camera " + str(camera_id) + " Mask", self.base_mask)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break

    def UpdateTracker(self, image):  # Work off a camera id or something, don't leave the detection for the user.
        x=10

    def DetectNewEntrants(self, image):
        # Returns new entrants within an image by running YOLO on the image after the application of the base mask
        # This results in only untracked objects being detected

        # masked_image = self.SubtractMaskFromImage(image, self.base_mask)
        masked_image = image.copy()
        return_status, classes, bounding_boxes, _ = OD.DetectObjectsInImage(image=masked_image)


        return return_status, classes, bounding_boxes

    def CreateNewTrackedObjectProcess(self, object_id, bounding_box, pipe):

        temp_tracked_object = TrackedObject(object_id, bounding_box)
        tracked_object_process = Process(target=temp_tracked_object.StartTracking, args=(pipe, ))
        tracked_object_process.start()

        return temp_tracked_object, tracked_object_process

    def AddObjectToTracker(self, name, identifier, bounding_box):
        tracked_object = [name, identifier, bounding_box]

        self.tracked_objects.append(TrackedObject(tracked_object=tracked_object))

    def RemoveObjectFromTracker(self, tracked_object):
        self.tracked_objects.remove(tracked_object)

    def AddParkingSpaceToTracker(self, parking_space_id, parking_space_bb):
        # Add parking space to tracker's list of parking space

        temp_space = ParkingSpace()
        temp_space.UpdateId(parking_space_id)
        temp_space.UpdateBB(parking_space_bb)

        self.parking_spaces.append(temp_space)

    def SubtractMaskFromImage(self, image, mask):
        # Takes an image and subtracts the provided mask from it
        # Returns the outcome of the subtraction

        masked_image = cv2.bitwise_and(image, image, mask=mask)


        return masked_image

    def AddToMask(self, tracked_object):
        # Takes a tracked object and adds its mask to the base mask
        # It should be noted that moving objects should continually remove their old mask and add their own

        if len(tracked_object.bounding_box) == 4:
            bounding_box = IU.GetPartialBoundingBox(bounding_box=tracked_object.bounding_box)
        else:
            bounding_box = tracked_object.bounding_box

        bounding_box_center = IU.GetBoundingBoxCenter(bounding_box=bounding_box)

        self.base_mask = IU.PlaceImage(base_image=self.base_mask,
                                       img_to_place=tracked_object.mask,
                                       center_x=bounding_box_center[0],
                                       center_y=bounding_box_center[1])

    def RemoveFromMask(self, tracked_object): # Change this in the future to not subtract adjacent masks
        # Takes a tracked object and removes its mask from the base mask
        # It should be noted that moving objects should continually remove their old mask and add their own

        if len(tracked_object.bounding_box) == 4:
            bounding_box = IU.GetPartialBoundingBox(bounding_box=tracked_object.bounding_box)
        else:
            bounding_box = tracked_object.bounding_box

        bounding_box_center = IU.GetBoundingBoxCenter(bounding_box=bounding_box)

        tracked_object_mask_height, tracked_object_mask_width, _ = tracked_object.mask.shape

        tracked_object.mask = np.zeros((tracked_object_mask_height, tracked_object_mask_width, 3), dtype='uint8')

        self.base_mask = IU.PlaceImage(base_image=self.base_mask,
                                       img_to_place=tracked_object.mask,
                                       center_x=bounding_box_center[0],
                                       center_y=bounding_box_center[1])

