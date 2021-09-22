from classes.system.super_classes.TrackedObjectListener import TrackedObjectListener
from classes.system.parking.ParkingSpace import ParkingSpace
from classes.system_utilities.helper_utilities import Constants
import json
import time

from multiprocessing import Process, shared_memory
import numpy as np
import sys


class ParkingTariffManager(TrackedObjectListener):
    def __init__(self, base_pool_size, new_object_in_pool_event):

        super().__init__(base_pool_size, new_object_in_pool_event)

        self.tariff_manager_process = 0
        self.should_keep_managing = True
        self.parking_spaces = []

    def LoadParkingSpacesFromJson(self):
        print("[ParkingTariffManager] Loading parking spaces from disk.", file=sys.stderr)
        with open(Constants.parking_spaces_json, 'r') as parking_json:
            parking_space_data = json.loads(parking_json.read())
            for parking_space in parking_space_data:
                self.parking_spaces.append(ParkingSpace(**parking_space))

    def AddParkingSpaceToManager(self, parking_space):
        self.parking_spaces.append(parking_space)

    def StartProcess(self):
        print("[ParkingTariffManager] Starting Parking Tariff Manager.", file=sys.stderr)
        self.tariff_manager_process = Process(target=self.StartManaging)
        self.tariff_manager_process.start()

    def StopProcess(self):
        self.tariff_manager_process.terminate()

    def StartManaging(self):
        super().Initialize()
        self.LoadParkingSpacesFromJson()

        while self.should_keep_managing:

            # stuff = self.GetAllActiveCameraIdAndLicensePlates()
            print(self.GetAllActiveTrackedProcessItems())
            # # Check if objects are entering/leaving parking spaces and update their status accordingly
            # for i in range(len(self.parking_spaces)):
            #     for j in range(len(tracked_object_bbs_shared_memory)):
            #         if self.parking_spaces[i].GetStatus() == ParkingStatus.OCCUPIED.value:
            #             # If the parking is occupied and the tracked object isn't the occupant, then continue
            #             if self.parking_spaces[i].GetOccupantId() != tracked_object_ids[j]:
            #                 continue
            #
            #         else:
            #             # If the parking is not occupied and the tracked object is stationary, then continue
            #             if tracked_object_movement_status[j] == TrackedObjectStatus.STATIONARY.value:
            #                 continue
            #
            #         # Hence, if the parking is occupied and the tracked object is the occupant, check if he's still in the parking
            #         # Hence, if the parking is not occupied and the object is moving, check if he's in this parking
            #
            #         # Check if the tracked object is in the parking
            #         is_car_in_parking = OD.IsCarInParkingBBN(self.parking_spaces[i].GetBB(), tracked_object_bbs_shared_memory[j].tolist())
            #
            #         # If it is, then update the parking to occupied, else, update it to unoccupied. Update the tracked object accordingly.
            #         # TODO: This should be updated to count down how long an object has been in a parking
            #         if is_car_in_parking:
            #             tracked_object_movement_status[j] = TrackedObjectStatus.STATIONARY.value
            #             self.parking_spaces[i].UpdateStatus(status=ParkingStatus.OCCUPIED.value)
            #             self.parking_spaces[i].UpdateOccupant(occupant_id=tracked_object_ids[j])
            #         else:
            #             tracked_object_movement_status[j] = TrackedObjectStatus.MOVING.value
            #             self.parking_spaces[i].UpdateStatus(status=ParkingStatus.NOT_OCCUPIED.value)
            #             self.parking_spaces[i].UpdateOccupant(occupant_id=-1)

            # self.CheckAndUpdateParkingStatuses()

            # print(stuff)
            time.sleep(1)

    def CheckAndUpdateParkingStatuses(self):
        # print(self.GetAllActiveBoundingBoxes())
        for i in range(len(self.parking_spaces)):
            x=10


