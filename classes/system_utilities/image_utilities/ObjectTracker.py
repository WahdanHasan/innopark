import classes.system_utilities.image_utilities.ObjectDetection as OD
import classes.system_utilities.image_utilities.ImageUtilities as IU
import cv2
import time
import numpy as np
from multiprocessing import Process, Manager, Value
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
    def __init__(self, tracked_object):
        # The objects_to_track variable must be in the list format of [name, identifier, bounding_box]
        # If the object is a vehicle, its id must be its license
        # It should be noted that the bounding box must be in the [TL, TR, BL, BR] format

        self.name = tracked_object[0]
        self.identifier = tracked_object[1]
        self.bounding_box = tracked_object[2]
        self.frames_since_last_seen = 0
        self.bounding_box_history = []
        self.mask = 0
        self.status = 0

    def UpdatePosition(self, new_bounding_box):
        old_bounding_box = self.bounding_box
        self.bounding_box = new_bounding_box
        self.bounding_box_history.append(old_bounding_box)

    def UpdateStatus(self, status):
        self.status = status

class Tracker:
    import time
    def __init__(self):
        #
        # height, width = camera.default_resolution[1], camera.default_resolution[0]
        #
        # self.base_mask = np.zeros((height, width, 3), dtype='uint8')
        # # self.base_mask = map(tuple, self.base_mask)
        # # self.base_mask = tuple(self.base_mask)

        self.tracker_process = 0
        self.parking_spaces = []

    def Start(self, camera_rtsp, camera_id):
        # All parking spots should be instantiated prior to calling this function

        # ADD MASK INITIALIZATION HERE !!!!!!!!!
        self.tracker_process = Process(target=self.Update, args=(camera_rtsp, camera_id))
        self.tracker_process.start()

    def Stop(self):
        # Sets the tracker continue to false then waits for it to stop
        self.tracker_process.terminate()

    def Update(self, camera_rtsp, camera_id):

        parking_space_boxes = []

        for i in range(len(self.parking_spaces)):
            parking_space_boxes.append(self.parking_spaces[i].bb)

        cam_parking = Camera(rtsp_link=camera_rtsp,
                             camera_id=camera_id)

        start_time = time.time()
        seconds_before_display = 1  # displays the frame rate every 1 second
        counter = 0
        while True:

            frame_parking = cam_parking.GetScaledNextFrame()

            parking_return_status, parking_classes, parking_bounding_boxes, parking_scores = OD.DetectObjectsInImage(frame_parking)

            # if parking_return_status == True:
            frame_yolo = IU.DrawBoundingBoxAndClasses(image=frame_parking,
                                                      class_names=parking_classes,
                                                      probabilities=parking_scores,
                                                      bounding_boxes=parking_bounding_boxes)


            parking_space_occupied_statuses = []
            if len(parking_space_boxes) != 0:
                for i in range(len(self.parking_spaces)):
                    parking_space_occupied_statuses.append(self.parking_spaces[i].is_occupied)

                # tl_br_bbs = []
                # for i in range(len(parking_space_boxes)):
                #     tl_br_bbs.append(IU.GetPartialBoundingBox(parking_space_boxes[i]))
                frame_yolo = IU.DrawParkingBoxes(frame_yolo, parking_space_boxes, parking_space_occupied_statuses)
                # frame_yolo = IU.DrawBoundingBoxes(frame_yolo, tl_br_bbs, color=(0, 0, 255) if parking_space_occupied_statuses else (0, 255, 0), thickness=3)

            for i in range(len(self.parking_spaces)):
                for j in range(len(parking_bounding_boxes)):
                    if OD.IsCarInParkingBB(parking_space_boxes[j], self.parking_spaces[i].bb):
                        self.parking_spaces[i].is_occupied = True


            cv2.imshow("Camera " + str(camera_id) + " YOLO Detection", frame_yolo)

            cv2.imshow("Camera " + str(camera_id) + " view", frame_parking)

            counter += 1
            if (time.time() - start_time) > seconds_before_display:
                print("Camera " + str(camera_id) + " FPS: ", counter / (time.time() - start_time))
                counter = 0
                start_time = time.time()

            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break

    def UpdateTracker(self, image):  # Work off a camera id or something, don't leave the detection for the user.
        x=10

    def DetectNewEntrants(self, image):
        # Returns new entrants within an image by running YOLO on the image after the application of the base mask
        # This results in only untracked objects being detected

        masked_image = self.SubtractMaskFromImage(image, self.base_mask)

        return_status, classes, bounding_boxes, _ = OD.DetectObjectsInImage(image=masked_image)


        return return_status, classes, bounding_boxes

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

