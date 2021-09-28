from classes.system.super_classes.TrackedObjectListener import TrackedObjectListener
from classes.system.parking.ParkingSpace import ParkingSpace
from classes.system_utilities.helper_utilities import Constants
from classes.system_utilities.helper_utilities.Enums import ParkingStatus
from classes.system_utilities.image_utilities import ImageUtilities as IU

from multiprocessing import Process
import cv2
import sys
import json
import time


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

            # time.sleep(0.1)
            if cv2.waitKey(17) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break

    def CheckAndUpdateParkingStatuses(self, ids, bbs):
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



    def PresentDebugItems(self, ids, bbs):

        for i in range(self.amount_of_trackers):
            temp_frame = self.GetTrackerFrameByTrackerId(i).copy()

            temp_parking_space_bbs = []
            temp_parking_is_occupied_list = []
            for j in range(len(self.parking_spaces)):
                if Constants.CAMERA_DETAILS[i][0] == self.parking_spaces[j].camera_id:
                    temp_parking_space_bbs.append(self.parking_spaces[j].bb)
                    temp_parking_is_occupied_list.append(self.parking_spaces[j].status)

            temp_frame = IU.DrawParkingBoxes(image=temp_frame,
                                             bounding_boxes=temp_parking_space_bbs,
                                             are_occupied=temp_parking_is_occupied_list)

            if ids is not None and bbs is not None:
                temp_active_ids = []
                temp_active_bbs = []
                for j in range(len(bbs)):
                    if ids[0][j] == i:
                        temp_active_bbs.append(bbs[j])
                        temp_active_ids.append(ids[2][j])

                temp_frame = IU.DrawBoundingBoxAndClasses(image=temp_frame,
                                                          class_names=temp_active_ids,
                                                          bounding_boxes=temp_active_bbs)



            cv2.imshow("[ParkingTariffManager] Camera " + str(i) + " view", temp_frame)










