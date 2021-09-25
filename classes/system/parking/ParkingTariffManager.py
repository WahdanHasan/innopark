from classes.system.super_classes.TrackedObjectListener import TrackedObjectListener
from classes.system.parking.ParkingSpace import ParkingSpace
from classes.system_utilities.helper_utilities import Constants
from classes.system_utilities.helper_utilities.Enums import ParkingStatus
from classes.system_utilities.helper_utilities.Enums import TrackedObjectStatus
from classes.system_utilities.image_utilities import ImageUtilities as IU
import json
import time
import cv2

from multiprocessing import Process
import sys


class ParkingTariffManager(TrackedObjectListener):
    def __init__(self, amount_of_trackers, base_pool_size, new_object_in_pool_event, seconds_parked_before_charge, is_debug_mode=False):

        super().__init__(amount_of_trackers, base_pool_size, new_object_in_pool_event)

        self.seconds_parked_before_charge = seconds_parked_before_charge
        self.tariff_manager_process = 0
        self.should_keep_managing = True
        self.parking_spaces = []
        self.is_debug_mode = is_debug_mode

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

            ids, bbs = self.GetAllActiveTrackedProcessItems()

            self.CheckAndUpdateParkingStatuses(ids=ids,
                                               bbs=bbs)

            if self.is_debug_mode:
                self.PresentDebugItems(ids=ids,
                                       bbs=bbs)

            time.sleep(0.5)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break

    def CheckAndUpdateParkingStatuses(self, ids, bbs):

        if not ids:
            return

        for i in range(len(bbs)):
            for j in range(len(self.parking_spaces)):
                if ids[1][i] != self.parking_spaces[j].GetCameraId():
                    continue

                # if



        # for i in range(len(self.parking_spaces)):
        #     for j in range(len(self.shared_memory_bbs)):
        #         if self.parking_spaces[i].GetStatus() == ParkingStatus.OCCUPIED.value:
        #             # If the parking is occupied and the tracked object isn't the occupant, then continue
        #             if self.parking_spaces[i].GetOccupantId() != ids[0][j]:
        #                 continue
        #
        #         else:
        #             # If the parking is not occupied and the tracked object is stationary, then continue
        #             if tracked_object_movement_status[j] == TrackedObjectStatus.STATIONARY.value:
        #                 continue




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

    def PresentDebugItems(self, ids, bbs):


        for i in range(self.amount_of_trackers):
            temp_frame = self.GetTrackerFrameByTrackerId(i).copy()

            if ids is not None:
                temp_active_ids = []
                temp_active_bbs = []
                for j in range(len(bbs)):
                    if ids[0][j] == i:
                        temp_active_bbs.append(bbs[j])
                        temp_active_ids.append(ids[2][j])

                temp_frame = IU.DrawBoundingBoxAndClasses(image=temp_frame,
                                                          class_names=temp_active_ids,
                                                          bounding_boxes=temp_active_bbs)

            temp_parking_space_bbs = []
            temp_parking_is_occupied_list = []
            for j in range(len(self.parking_spaces)):
                if Constants.CAMERA_DETAILS[i][0] == self.parking_spaces[j].GetCameraId():
                    temp_parking_space_bbs.append(self.parking_spaces[j].GetBB())
                    temp_parking_is_occupied_list.append(self.parking_spaces[j].GetStatus())

            temp_frame = IU.DrawParkingBoxes(image=temp_frame,
                                             bounding_boxes=temp_parking_space_bbs,
                                             are_occupied=temp_parking_is_occupied_list)

            cv2.imshow("[ParkingTariffManager] Camera " + str(i) + " view", temp_frame)










