from threading import Thread
from multiprocessing import shared_memory
from classes.system_utilities.helper_utilities import Constants
import numpy as np

class ObjectTrackerListener:
    def __init__(self, base_pool_size):
        # self.new_object_in_pool_event = new_object_in_pool_event
        self.base_pool_size = base_pool_size
        self.should_keep_listening_for_new_object = True

        self.new_object_in_pool_event_listener_thread = 0
        self.tracked_object_bbs_shared_memory = []

        self.Initialize()

    def Initialize(self):
        self.CreateReferencesToPoolBBs()
        # self.new_object_in_pool_event_listener_thread = Thread(target=self.ListenForNewObjectInPool)

    def CreateReferencesToPoolBBs(self):

        for i in range(self.base_pool_size):
            # print(Constants.bb_shared_memory_manager_prefix + str(i))
            # temp_shm = shared_memory.SharedMemory(name=Constants.bb_shared_memory_manager_prefix + str(i))

            temp_bb = np.ndarray(shape=np.asarray(Constants.bb_example, dtype=np.int32).shape,
                                 dtype=np.int32,
                                 buffer=shared_memory.SharedMemory(name=Constants.bb_shared_memory_manager_prefix + str(i)).buf)

            self.tracked_object_bbs_shared_memory.append(temp_bb)
        x=10
    # def ListenForNewObjectInPool(self):
    #     while self.should_keep_listening_for_new_object:
    #         self.new_object_in_pool_event.wait()


