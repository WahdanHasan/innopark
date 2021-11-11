from classes.super_classes.TrackedObjectListener import TrackedObjectListener
from classes.super_classes.ShutDownEventListener import ShutDownEventListener
from classes.system.parking.ParkingSpace import ParkingSpace
from classes.system_utilities.helper_utilities import Constants
from classes.system_utilities.helper_utilities.Enums import ParkingStatus
from classes.system_utilities.image_utilities import ImageUtilities as IU
from classes.system_utilities.data_utilities.Avenues import GetAllParkings

from multiprocessing import Process, shared_memory
import numpy as np
import sys
import json
import time


class ParkingTariffManager(TrackedObjectListener, ShutDownEventListener):
    def __init__(self, amount_of_trackers, new_object_in_pool_event, seconds_parked_before_charge, shutdown_event, start_system_event):

        TrackedObjectListener.__init__(self, amount_of_trackers, new_object_in_pool_event)
        ShutDownEventListener.__init__(self, shutdown_event)

        self.seconds_parked_before_charge = seconds_parked_before_charge
        self.shutdown_event = shutdown_event
        self.start_system_event = start_system_event
        self.tariff_manager_process = 0
        self.should_keep_managing = True
        self.parking_spaces = []
        self.is_debug_mode = True
        self.base_blank = np.zeros(shape=(Constants.default_camera_shape[1], Constants.default_camera_shape[0], Constants.default_camera_shape[2]), dtype=np.uint8)
        self.frame_shms = []
        self.frames = []

    def createSharedMemoryStuff(self, amount_of_trackers):
        for i in range(amount_of_trackers):
            temp_shm = shared_memory.SharedMemory(create=True,
                                                  name=Constants.parking_tariff_management_shared_memory_prefix + str(i),
                                                  size=self.base_blank.nbytes)

            temp_frame = np.ndarray(self.base_blank.shape, dtype=np.uint8, buffer=temp_shm.buf)
            self.frame_shms.append(temp_shm)
            self.frames.append(temp_frame)

    def loadParkingSpacesFromJson(self):
        with open(Constants.parking_spaces_json, 'r') as parking_json:
            parking_space_data = json.loads(parking_json.read())
            for parking_space in parking_space_data:
                self.parking_spaces.append(ParkingSpace(**parking_space))

    def loadParkingSpacesFromDb(self):
        parkings_ids, parkings_docs = GetAllParkings(Constants.avenue_id)

        for i in range(len(parkings_ids)):
            parking_doc = parkings_docs[i]
            parking_id = parkings_ids[i]

            self.parking_spaces.append(ParkingSpace(parking_doc[Constants.camera_id_key], parking_id,
                                                    parking_doc[Constants.bounding_box_key], parking_doc[Constants.is_occupied_key],
                                                    parking_doc[Constants.parking_type_key], parking_doc[Constants.rate_per_hour_key]))

    def addParkingSpaceToManager(self, parking_space):
        self.parking_spaces.append(parking_space)

    def startProcess(self):
        print("[ParkingTariffManager] Starting Parking Tariff Manager.", file=sys.stderr)
        self.tariff_manager_process = Process(target=self.startManaging)
        self.tariff_manager_process.start()

    def stopProcess(self):
        self.tariff_manager_process.terminate()

    def startManaging(self):
        TrackedObjectListener.initialize(self)
        ShutDownEventListener.initialize(self)
        # self.loadParkingSpacesFromJson()
        self.loadParkingSpacesFromDb()
        self.createSharedMemoryStuff(self.amount_of_trackers)

        self.start_system_event.wait()

        while self.should_keep_managing:

            if not self.shutdown_should_keep_listening:
                print("[ParkingTariffManager] Cleaning up.", file=sys.stderr)
                self.cleanUp()
                return

            ids, bbs = self.getAllActiveTrackedProcessItems()

            self.checkAndUpdateParkingStatuses(ids=ids,
                                               bbs=bbs)

            if self.is_debug_mode:
                self.writeDebugItems()

            time.sleep(0.033)

    def checkAndUpdateParkingStatuses(self, ids, bbs):
        # An object tracker cannot be on the id 0
        if not ids or ids is None:
            return

        if not bbs or bbs is None:
            return

        for i in range(len(bbs)):
            for j in range(len(self.parking_spaces)):
                if ids[1][i] != self.parking_spaces[j].camera_id:
                    continue

                car_is_in_this_parking = IU.AreBoxesOverlappingTF(parking_bounding_box=self.parking_spaces[j].bb,
                                                                  car_bounding_box=bbs[i])

                temp_parking = self.parking_spaces[j]

                if temp_parking.occupant_id == ids[2][i]:
                    if temp_parking.status == ParkingStatus.OCCUPIED:
                        if car_is_in_this_parking:
                            temp_parking.occupant_left_parking_time_start = 0
                        else:
                            temp_parking.CheckAndUpdateIfOccupantLeft()

                    elif temp_parking.status == ParkingStatus.NOT_OCCUPIED:
                        if car_is_in_this_parking:
                            temp_parking.CheckAndUpdateIfConsideredParked()
                        else:
                            temp_parking.ResetOccupant()

                elif temp_parking.status == ParkingStatus.NOT_OCCUPIED:
                    if car_is_in_this_parking:
                        temp_parking.occupant_park_time_start = time.time()
                        temp_parking.UpdateOccupantId(ids[2][i])

    def writeDebugItems(self):

        for i in range(self.amount_of_trackers):
            temp_frame = self.base_blank.copy()

            temp_parking_space_bbs = []
            temp_parking_is_occupied_list = []
            for j in range(len(self.parking_spaces)):
                if Constants.CAMERA_DETAILS[i][0] == self.parking_spaces[j].camera_id:
                    temp_parking_space_bbs.append(self.parking_spaces[j].bb)
                    temp_parking_is_occupied_list.append(self.parking_spaces[j].status)

            temp_frame = IU.DrawParkingBoxes(image=temp_frame,
                                             bounding_boxes=temp_parking_space_bbs,
                                             are_occupied=temp_parking_is_occupied_list)

            self.frames[i][:] = temp_frame[:]

    def cleanUp(self):
        for shm in self.frame_shms:
            shm.unlink()
