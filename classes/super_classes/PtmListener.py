from multiprocessing import shared_memory
from classes.system_utilities.helper_utilities import Constants
from classes.system_utilities.helper_utilities.Enums import ParkingStatus
import numpy as np

class PtmListener:
    def __init__(self):
        self.amount_of_frames = len(Constants.CAMERA_DETAILS)

        self.shared_memory_frames = []
        self.shared_memory_frame_managers = []
        self.shared_memory_items = []
        self.shared_memory_item_managers = []

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

        import json

        parking_spaces_count = 0

        with open(Constants.parking_spaces_json, 'r') as parking_json:
            parking_space_data = json.loads(parking_json.read())
            for parking_space in parking_space_data:
                parking_spaces_count += 1

        for i in range(parking_spaces_count):
            temp_shm_items = shared_memory.SharedMemory(name=Constants.parking_space_shared_memory_prefix + str(i))
            temp_items = np.ndarray(shape=np.asarray(Constants.ptm_debug_items_example, dtype=np.uint8).shape,
                                    dtype=np.uint8,
                                    buffer=temp_shm_items.buf)

            self.shared_memory_item_managers.append(temp_shm_items)
            self.shared_memory_items.append(temp_items)

    def getOccupiedParkingSpaceItems(self):
        return self.getOccupiedParkingSpaceIds(), self.getOccupiedParkingSpaceOccupantIds()

    def getOccupiedParkingSpaceIds(self):

        temp_occupied_id_list = []

        for i in range(len(self.shared_memory_items)):
            if bool(self.shared_memory_items[i][1]) == ParkingStatus.OCCUPIED.value:
                temp_occupied_id_list.append(self.shared_memory_items[i][0])

        # If list is empty, return none, else return the list
        if not temp_occupied_id_list:
            return None
        else:
            return temp_occupied_id_list

    def getOccupiedParkingSpaceOccupantIds(self):

        temp_occupied_id_list = []

        for i in range(len(self.shared_memory_items)):
            if bool(self.shared_memory_items[i][1]) == ParkingStatus.OCCUPIED.value:
                temp_occupied_id_list.append(''.join('' if i == 0 else chr(i) for i in self.shared_memory_items[i][2:]))

        # If list is empty, return none, else return the list
        if not temp_occupied_id_list:
            return None
        else:
            return temp_occupied_id_list

    def getFrameByCameraId(self, camera_id):
        return self.shared_memory_frames[camera_id]
