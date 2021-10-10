from multiprocessing import shared_memory
from classes.system_utilities.helper_utilities import Constants
import numpy as np

class ObjectTrackerListener:
    def __init__(self, amount_of_trackers):
        self.amount_of_trackers = amount_of_trackers

        self.shared_memory_tracker_frames = []
        self.shared_memory_tracker_frame_managers = []

        self.shared_memory_tracker_masks = []
        self.shared_memory_tracker_mask_managers = []

    def Initialize(self):
        self.CreateReferenceToObjectTrackerItems()

    def CreateReferenceToObjectTrackerItems(self):

        for i in range(self.amount_of_trackers):
            # Get shared memory object tracker frames
            temp_shm_frame = shared_memory.SharedMemory(name=Constants.frame_shared_memory_prefix + str(i))
            temp_frame = np.ndarray(shape=(Constants.default_camera_shape[1], Constants.default_camera_shape[0], Constants.default_camera_shape[2]),
                                    dtype=np.uint8,
                                    buffer=temp_shm_frame.buf)

            self.shared_memory_tracker_frames.append(temp_frame)
            self.shared_memory_tracker_frame_managers.append(temp_shm_frame)

            # Get shared memory object tracker masks
            temp_shm_mask = shared_memory.SharedMemory(name=Constants.object_tracker_mask_shared_memory_prefix + str(i))
            temp_mask = np.ndarray(shape=(Constants.default_camera_shape[1], Constants.default_camera_shape[0]),
                                   dtype=np.uint8,
                                   buffer=temp_shm_mask.buf)

            self.shared_memory_tracker_masks.append(temp_mask)
            self.shared_memory_tracker_mask_managers.append(temp_shm_mask)

    def GetTrackerFrameByTrackerId(self, tracker_id):
        return self.shared_memory_tracker_frames[tracker_id]
