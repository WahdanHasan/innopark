import classes.system_utilities.image_utilities.ObjectDetection as OD
import classes.system_utilities.image_utilities.ImageUtilities as IU
import cv2
import numpy as np
from classes.enum_classes.Enums import ObjectStatus

class TrackedObject:
    def __init__(self, tracked_object):
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

    def __init(self, camera):
        # The objects_to_track variable must be in the list format of [type, id, bounding_box]
        # If the object is a vehicle, its id must be its license
        # It should be noted that the bounding box must be in the [TL, TR, BL, BR] format

        frame = camera.GetCurrentFrame()
        height, width, _ = frame.shape

        self.base_mask = np.zeros((height, width, 1))

        self.tracked_objects = []

        self.camera = camera


    def UpdateTracker(self, new_bounding_boxes):  # Work off a camera id or something, don't leave the detection for the user.
        x=10

    def DetectNewEntrants(self, image):
        # Returns new entrants within an image by running YOLO on the image after the application of the base mask
        # This results in only untracked objects being detected

        masked_image = self.SubtractMaskFromImage(image, self.base_mask)

        return_status, classes, bounding_boxes, scores = OD.DetectObjectsInImage(image=masked_image)

        return return_status, classes, bounding_boxes, scores

    def SubtractMaskFromImage(self, image, mask):
        # Takes an image and subtracts the provided mask from it
        # Returns the outcome of the subtraction

        masked_image = cv2.abs(image, mask)
        # masked_image = cv2.subtract(image, mask)
        # masked_image = image - mask

        return masked_image

    def AddToMask(self, tracked_object, mask):
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


    def RemoveFromMask(self, tracked_object, mask):
        # Takes a tracked object and removes its mask from the base mask
        # It should be noted that moving objects should continually remove their old mask and add their own

        mask = cv2.abs(mask, tracked_object.mask)
        # mask = cv2.subtract(mask, tracked_object.mask)
        # mask = mask - tracked_object.mask



    # def DetectNewEntrants(self, image):
