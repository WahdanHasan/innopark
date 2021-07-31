import classes.system_utilities.image_utilities.ObjectDetection as OD
import classes.system_utilities.image_utilities.ImageUtilities as IU

class TrackedObject:
    def __init__(self, tracked_object):
        self.type = []
        self.type.append(tracked_object[0])
        self.id = []
        self.id.append(tracked_object[1])
        self.bounding_box = tracked_object[2]
        self.frames_since_last_seen = 0
        self.bounding_box_history = []


    def UpdatePosition(self, new_bounding_box):
        old_bounding_box = self.bounding_box
        self.bounding_box = new_bounding_box
        self.bounding_box_history.append(old_bounding_box)

class Tracker:

     def __init(self, objects_to_track):
         # The objects_to_track variable must be in the list format of [type, id, bounding_box]
         # If the object is a vehicle, its id must be its license
         # It should be noted that the bounding box must be in the [TL, TR, BL, BR] format

         self.tracked_objects = []

         objects_size = len(objects_to_track)

         for i in range(objects_size):
             temp_object = TrackedObject(objects_to_track[i])

             self.tracked_objects.append(temp_object)

    def UpdateTracker(self, new_bounding_boxes):


        # Find the center points for the new bounding boxes
        new_box_center_point_list = []
        new_bounding_boxes_length = len(new_bounding_boxes)
        for i in range(new_bounding_boxes_length):
            temp_center_point = IU.GetBoundingBoxCenter(new_bounding_boxes[i])
            new_box_center_point_list.append(temp_center_point)


        tracked_objects_length = len(self.tracked_objects)
        for i in range(tracked_objects_length):

            # Create a reference to the tracked object on the current iteration
            tracked_object = self.tracked_objects[i]

            # Get the tracked object's bounding box center point
            tracked_object_center_point = IU.GetFullBoundingBoxCenter(tracked_object[2])




    def GetNewObjectIndexes(self, object_ids, array_size):
        # Takes the id array of the new objects and the size of the array
        # Checks if a tracked object's ids exist
        # Returns the indexes of the new objects
        # *Comment so i dont forget*: I'll associate each object with its new position, left out boxes are what im
        # finding through this function

        new_object_indexes = []
        for i in range (array_size):
            for tracked_object_id in self.tracked_objects[1][i]:
                for untracked_object_id in object_ids:
                    if tracked_object_id == untracked_object_id:
                        continue
                    new_object_indexes.append(i)

        return new_object_indexes

