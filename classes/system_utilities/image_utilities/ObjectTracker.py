import classes.system_utilities.image_utilities.ObjectDetection as OD
import classes.system_utilities.image_utilities.ImageUtilities as IU
import cv2
import numpy as np
from classes.enum_classes.Enums import ObjectStatus

class TrackedObject:
    def __init__(self, tracked_object):
        # The objects_to_track variable must be in the list format of [type, id, bounding_box]
        # If the object is a vehicle, its id must be its license
        # It should be noted that the bounding box must be in the [TL, TR, BL, BR] format

        self.type = tracked_object[0]
        self.id = tracked_object[1]
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

    def __init__(self, camera):

        frame = camera.GetCurrentFrame()
        height, width, _ = frame.shape

        self.base_mask = np.zeros((height, width, 3), dtype='uint8')
        # self.base_mask = map(tuple, self.base_mask)
        # self.base_mask = tuple(self.base_mask)

        self.tracked_objects = []

        self.camera = camera


    def UpdateTracker(self, image):  # Work off a camera id or something, don't leave the detection for the user.
        x=10

    def DetectNewEntrants(self, image):
        # Returns new entrants within an image by running YOLO on the image after the application of the base mask
        # This results in only untracked objects being detected

        masked_image = self.SubtractMaskFromImage(image, self.base_mask)

        return_status, classes, bounding_boxes, scores = OD.DetectObjectsInImage(image=masked_image)


        return return_status, classes, bounding_boxes, scores

    def AddObjectToTracker(self, type, id, bounding_box):
        tracked_object = [type, id, bounding_box]

        tracked_object = TrackedObject(tracked_object=tracked_object)

        self.tracked_objects.append(tracked_object)

    def RemoveObjectFromTracker(self, tracked_object):
        self.tracked_objects.remove(tracked_object)

    def SubtractMaskFromImage(self, image, mask):
        # Takes an image and subtracts the provided mask from it
        # Returns the outcome of the subtraction

        masked_image = cv2.subtract(image, mask)


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

