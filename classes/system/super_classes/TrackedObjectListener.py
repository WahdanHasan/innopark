from threading import Thread
from multiprocessing import shared_memory
from classes.system_utilities.helper_utilities import Constants
import numpy as np

class TrackedObjectListener:
    def __init__(self, base_pool_size, new_object_in_pool_event):
        self.pool_size = base_pool_size
        self.new_object_in_pool_event_listener_thread = 0
        self.new_object_in_pool_event = new_object_in_pool_event
        self.should_keep_listening_for_new_object = False

        self.shared_memory_bbs = []
        self.shared_memory_bb_managers = []

        self.shared_memory_ids = []
        self.shared_memory_id_managers = []

    def Initialize(self):
        self.CreateReferencesToPoolBBs()

    def CreateReferencesToPoolBBs(self):

        # Get bbs and ids from memory
        for i in range(self.pool_size):
            temp_shm_bb = shared_memory.SharedMemory(name=(Constants.bb_shared_memory_manager_prefix + str(i)))

            temp_bb = np.ndarray(shape=np.asarray(Constants.bb_example, dtype=np.int32).shape,
                                 dtype=np.int32,
                                 buffer=temp_shm_bb.buf)

            self.shared_memory_bbs.append(temp_bb)
            self.shared_memory_bb_managers.append(temp_shm_bb)

            temp_shm_ids = shared_memory.SharedMemory(name=Constants.tracked_process_ids_prefix + str(i))

            temp_ids = np.ndarray(shape=np.asarray(Constants.tracked_process_ids_example, dtype=np.uint8).shape,
                                  dtype=np.uint8,
                                  buffer=temp_shm_ids.buf)

            self.shared_memory_ids.append(temp_ids)
            self.shared_memory_id_managers.append(temp_shm_ids)

    def ListenForNewObjectInPool(self):

        while self.should_keep_listening_for_new_object:
            self.new_object_in_pool_event.wait()

            temp_shm_manager = shared_memory.SharedMemory(create=False,
                                                          name=(Constants.bb_shared_memory_manager_prefix + str(self.pool_size)))

            temp_bb = np.ndarray(np.asarray(Constants.bb_example, dtype=np.int16).shape, dtype=np.int16, buffer=temp_shm_manager.buf)


            self.shared_memory_bb_managers.append(temp_shm_manager)
            self.shared_memory_bbs.append(temp_bb)

            temp_shm_ids_manager = shared_memory.SharedMemory(create=False,
                                                              name=(Constants.tracked_process_ids_prefix + str(self.pool_size)))

            temp_ids = np.ndarray(np.asarray(Constants.tracked_process_ids_example, dtype=np.uint8).shape, dtype=np.uint8, buffer=temp_shm_ids_manager.buf)

            self.shared_memory_id_managers.append(temp_shm_ids_manager)
            self.shared_memory_ids.append(temp_ids)

            self.pool_size += 1

    def GetAllActiveCameraIdAndLicensePlates(self):
        temp_camera_id_list = []
        temp_object_id_list = []

        for i in range(len(self.shared_memory_ids)):
            # If the camera id is set to the default, continue
            if self.shared_memory_ids[i][0] == Constants.tracked_process_ids_example[0]:
                continue

            temp_list = self.IntegerTrackedObjectIdsToAscii(self.shared_memory_ids[i])

            temp_camera_id_list.append(temp_list[0])
            temp_object_id_list.append(temp_list[1])

        # If list is empty, return none, else return list
        if not temp_camera_id_list:
            return None
        else:
            return temp_camera_id_list, temp_object_id_list

    def IntegerTrackedObjectIdsToAscii(self, camera_id_and_license_in_shared_memory):
        temp_list = camera_id_and_license_in_shared_memory.tolist()

        # If object id is none, return only the camera id, else, return both
        if temp_list[1] == Constants.tracked_process_ids_example[1]:
            return [int(temp_list[0]), None]
        else:
            # Convert all non 0 integers to ascii only
            return [int(temp_list[0]), ''.join('' if i == 0 else chr(i) for i in temp_list[1:])]

    def GetAllActiveBoundingBoxes(self):
        temp_active_bb_list = []

        for i in range(len(self.shared_memory_bbs)):
            # If box is set to default, continue
            if self.shared_memory_bbs[i][0][0].item() == Constants.bb_example[0][0]:
                continue

            temp_active_bb_list.append(self.shared_memory_bbs[i].tolist())

        # If list is empty, return none, else return the list
        if not temp_active_bb_list:
            return None
        else:
            return temp_active_bb_list

    def GetAllActiveTrackedProcessItems(self):
        return self.GetAllActiveCameraIdAndLicensePlates(), self.GetAllActiveBoundingBoxes()