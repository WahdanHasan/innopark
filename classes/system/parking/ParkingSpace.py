from classes.system_utilities.helper_utilities.Enums import ParkingStatus
from classes.system_utilities.data_utilities import SMS
from classes.system_utilities.helper_utilities import Constants
from classes.system_utilities.data_utilities import Avenues
from threading import Thread

import numpy as np
from datetime import timedelta, datetime
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
        self.start_datetime = 0
        self.end_datetime = 0
        self.session_id = 0


        self.ResetOccupant()

    def ResetOccupant(self):
        self.occupant_park_time_start = 0
        self.occupant_left_parking_time_start = 0
        self.occupant_id = -1
        self.status = ParkingStatus.NOT_OCCUPIED
        self.start_datetime = 0
        self.end_datetime = 0
        self.session_id = 0

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
            self.start_datetime = datetime.now()
            self.session_id = Avenues.AddSession(avenue=Constants.avenue_id,
                                                 vehicle=self.occupant_id,
                                                 parking_id=self.parking_id,
                                                 start_datetime=self.start_datetime)

    def CheckAndUpdateIfOccupantLeft(self):

        if self.occupant_left_parking_time_start == 0:
            self.occupant_left_parking_time_start = time.time()

        if (time.time() - self.occupant_left_parking_time_start) >= self.seconds_before_considered_left:
            t1 = Thread(target=self.ChargeOccupant())
            t1.start()

    def ChargeOccupant(self):
        self.end_datetime = datetime.now()
        end_datetime = self.end_datetime
        start_datetime = self.start_datetime
        session_id = self.session_id
        occupant_id = self.occupant_id
        self.ResetOccupant()

        print("Occupant with id " + str(occupant_id) + " will now be charged", file=sys.stderr)


        time_elapsed = end_datetime - start_datetime

        tariff_amount = int(np.ceil(time_elapsed.seconds/Constants.seconds_in_hour) * self.rate_per_hour)

        Avenues.UpdateSession(avenue=Constants.avenue_id,
                              session_id=session_id,
                              end_datetime=end_datetime,
                              tariff_amount=tariff_amount)

        SMS.sendSmsToLicense(license_plate=occupant_id,
                             tariff_amount=tariff_amount)

    def CalculateSessionTariffAmount(self, start_datetime, end_datetime, rate_per_hour):

        start_day = int(start_datetime.strftime('%d'))
        end_day = int(end_datetime.strftime('%d'))
        subtracted_day = end_day - start_day

        start_time = timedelta(hours=start_datetime.hour, minutes=start_datetime.minute, seconds=start_datetime.second)
        end_time = timedelta(hours=end_datetime.hour, minutes=end_datetime.minute, seconds=end_datetime.second)
        subtracted_time = end_time - start_time

        tariff_amount = int(np.ceil(subtracted_time.seconds/Constants.seconds_in_hour) * rate_per_hour)

        if (subtracted_day > 0):
            tariff_amount += 24 * rate_per_hour

        return tariff_amount