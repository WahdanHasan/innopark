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

        self.Initialize()

    def Initialize(self):

        self.CreateReferencesToPoolBBs()

        self.new_object_in_pool_event_listener_thread = Thread(target=self.ListenForNewObjectInPool)
        self.new_object_in_pool_event_listener_thread.daemon = True
        self.should_keep_listening_for_new_object = True
        self.new_object_in_pool_event_listener_thread.start()

    def CreateReferencesToPoolBBs(self):

        # Get bbs and ids from memory
        for i in range(self.pool_size):
            temp_shm_bb = shared_memory.SharedMemory(create=False,
                                                     name=(Constants.bb_shared_memory_manager_prefix + str(i)))

            temp_bb = np.ndarray(np.asarray(Constants.bb_example, dtype=np.int32).shape, dtype=np.int32, buffer=temp_shm_bb.buf)

            self.shared_memory_bbs.append(temp_bb)
            self.shared_memory_bb_managers.append(temp_shm_bb)

            temp_shm_ids = shared_memory.SharedMemory(create=False,
                                                      name=(Constants.tracked_process_ids_prefix + str(i)))

            temp_ids = np.ndarray(np.asarray(Constants.tracked_process_ids_example, dtype=np.int32).shape, dtype=np.int32, buffer=temp_shm_ids.buf)

            self.shared_memory_ids.append(temp_ids)
            self.shared_memory_id_managers.append(temp_shm_ids)

    def ListenForNewObjectInPool(self):

        while self.should_keep_listening_for_new_object:
            self.new_object_in_pool_event.wait()

            temp_shm_manager = shared_memory.SharedMemory(create=False,
                                                          name=(Constants.bb_shared_memory_manager_prefix + str(self.pool_size)))

            temp_bb = np.ndarray(np.asarray(Constants.bb_example, dtype=np.int32).shape, dtype=np.int32, buffer=temp_shm_manager.buf)


            self.shared_memory_bb_managers.append(temp_shm_manager)
            self.shared_memory_bbs.append(temp_bb)

            temp_shm_ids_manager = shared_memory.SharedMemory(create=False,
                                                              name=(Constants.tracked_process_ids_prefix + str(self.pool_size)))

            temp_ids = np.ndarray(np.asarray(Constants.bb_example, dtype=np.int32).shape, dtype=np.int32, buffer=temp_shm_ids_manager.buf)

            self.shared_memory_id_managers.append(temp_shm_ids_manager)
            self.shared_memory_ids.append(temp_ids)

            self.pool_size += 1
