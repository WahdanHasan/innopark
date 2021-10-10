from multiprocessing import shared_memory
from classes.system_utilities.helper_utilities import Constants
import numpy as np

class PtmListener:
    def __init__(self):
        self.amount_of_frames = len(Constants.CAMERA_DETAILS)

        self.shared_memory_frames = []
        self.shared_memory_frame_managers = []

    def initialize(self):
        self.createReferenceToFrames()

    def createReferenceToFrames(self):

        for i in range(self.amount_of_frames):
            # Get shared memory object tracker frames
            temp_shm_frame = shared_memory.SharedMemory(name=Constants.parking_tariff_management_shared_memory_prefix + str(i))
            temp_frame = np.ndarray(shape=(Constants.default_camera_shape[1], Constants.default_camera_shape[0], Constants.default_camera_shape[2]),
                                    dtype=np.uint8,
                                    buffer=temp_shm_frame.buf)

            self.shared_memory_frames.append(temp_frame)
            self.shared_memory_frame_managers.append(temp_shm_frame)

    def getFrameByCameraId(self, camera_id):
        return self.shared_memory_frames[camera_id]
