from classes.super_classes.FramesListener import FramesListener
from classes.system_utilities.helper_utilities import Constants

from multiprocessing import shared_memory
import numpy as np

class ObjectTrackerListener(FramesListener):
    def __init__(self, amount_of_trackers):
        FramesListener.__init__(self)

        self.amount_of_trackers = amount_of_trackers

        self.shared_memory_tracker_masks = []
        self.shared_memory_tracker_mask_managers = []

        self.frame_offset_length = len(Constants.ENTRANCE_CAMERA_DETAILS)

    def initialize(self):
        FramesListener.initialize(self)
        self.createReferenceToObjectTrackerItems()

    def createReferenceToObjectTrackerItems(self):
        for i in range(self.amount_of_trackers):
            # Get shared memory object tracker masks
            temp_shm_mask = shared_memory.SharedMemory(name=Constants.object_tracker_mask_shared_memory_prefix + str(i + self.frame_offset_length))
            temp_mask = np.ndarray(shape=(Constants.default_camera_shape[1], Constants.default_camera_shape[0]),
                                   dtype=np.uint8,
                                   buffer=temp_shm_mask.buf)

            self.shared_memory_tracker_masks.append(temp_mask)
            self.shared_memory_tracker_mask_managers.append(temp_shm_mask)

    def getFrameByCameraId(self, camera_id):
        return self.shared_memory_frames[camera_id]
