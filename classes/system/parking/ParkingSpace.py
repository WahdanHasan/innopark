from classes.system_utilities.helper_utilities.Enums import ParkingStatus
from classes.system_utilities.data_utilities import SMS

import sys
import time

class ParkingSpace:
    def __init__(self, camera_id, parking_id, bounding_box, is_occupied, parking_type, rate_per_hour, seconds_before_considered_parked=2, seconds_before_considered_left=2):
        # DB initialized variables
        self.camera_id = camera_id
        self.parking_id = parking_id
        self.bb = bounding_box
        self.is_occupied = is_occupied
        self.parking_type = parking_type
        self.rate_per_hour = rate_per_hour

        # Default initialized variables
        self.seconds_before_considered_parked = seconds_before_considered_parked
        self.seconds_before_considered_left = seconds_before_considered_left
        self.occupant_park_time_start = 0
        self.occupant_left_parking_time_start = 0
        self.occupant_id = 0
        self.status = 0

        self.ResetOccupant()

    def ResetOccupant(self):
        self.occupant_park_time_start = 0
        self.occupant_left_parking_time_start = 0
        self.occupant_id = -1
        self.status = ParkingStatus.NOT_OCCUPIED

    def UpdateId(self, new_parking_id):
        self.parking_id = new_parking_id

    def UpdateOccupantId(self, occupant_id):
        self.occupant_id = occupant_id

    def UpdateCameraId(self, camera_id):
        self.camera_id = camera_id

    def UpdateBB(self, new_bb):
        # [TL, TR, BL, BR]
        self.bb = new_bb

    def UpdateStatus(self, status):
        self.status = status

    def CheckAndUpdateIfConsideredParked(self):
        if (time.time() - self.occupant_park_time_start) >= self.seconds_before_considered_parked:
            self.status = ParkingStatus.OCCUPIED
            self.occupant_park_time_start = time.time()

    def CheckAndUpdateIfOccupantLeft(self):

        if self.occupant_left_parking_time_start == 0:
            self.occupant_left_parking_time_start = time.time()

        if (time.time() - self.occupant_left_parking_time_start) >= self.seconds_before_considered_left:
            self.ChargeOccupant()
            self.ResetOccupant()

    def ChargeOccupant(self):
        print("Occupant with id " + str(self.occupant_id) + " will now be charged", file=sys.stderr)

        SMS.sendSmsToLicense(self.occupant_id)
