import classes.system_utilities.image_utilities.ObjectDetection as OD

class TrackedObject:
    def __init__(self, tracked_object):
        self.type = tracked_object[0]
        self.id = tracked_object[1]
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



