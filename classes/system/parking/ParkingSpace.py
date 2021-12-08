from classes.system_utilities.helper_utilities.Enums import ParkingStatus, ReturnStatus
from classes.system_utilities.data_utilities import SMS
from classes.system_utilities.helper_utilities import Constants
from classes.system_utilities.data_utilities import Avenues
from threading import Thread
from multiprocessing import shared_memory, Pipe

import numpy as np
from datetime import timedelta, datetime
import sys
import time

class ParkingSpace:
    def __init__(self, internal_id, camera_id, parking_id, bounding_box, occupancy_box, is_occupied, parking_type, rate_per_hour, seconds_before_considered_parked=2, seconds_before_considered_left=2):
        # DB initialized variables
        self.camera_id = camera_id
        self.parking_id = parking_id
        self.bb = bounding_box
        self.ob = occupancy_box
        self.is_occupied = is_occupied
        self.parking_type = parking_type
        self.rate_per_hour = rate_per_hour

        # Default initialized variables
        self.internal_id = internal_id
        self.seconds_before_considered_parked = seconds_before_considered_parked
        self.seconds_before_considered_left = seconds_before_considered_left
        self.occupant_park_time_start = 0
        self.occupant_left_parking_time_start = 0
        self.occupant_id = 0
        self.status = 0
        self.start_datetime = 0
        self.end_datetime = 0
        self.session_id = 0
        self.shared_memory_manager = 0
        self.shared_memory_items = 0

        self.resetOccupant()

    def __iter__(self):
        yield 'internal_id', self.internal_id
        yield 'is_occupied', self.is_occupied
        yield 'camera_id', self.camera_id
        yield 'parking_id', self.parking_id
        yield 'parking_type', self.parking_type
        yield 'rate_per_hour', self.rate_per_hour
        yield 'bounding_box', self.bb
        yield 'occupancy_box', self.ob

    def createSharedMemoryItems(self):
        self.shared_memory_manager = shared_memory.SharedMemory(create=True,
                                                                name=Constants.parking_space_shared_memory_prefix + str(self.internal_id),
                                                                size=np.asarray(Constants.ptm_debug_items_example, dtype=np.uint16).nbytes)

        self.shared_memory_items = np.ndarray(shape=np.asarray(Constants.ptm_debug_items_example, dtype=np.uint16).shape,
                                              dtype=np.uint16,
                                              buffer=self.shared_memory_manager.buf)

        # Only supports int parking ids currently
        self.shared_memory_items[0] = int(self.parking_id)
        self.shared_memory_items[1] = int(self.is_occupied)

    def resetOccupant(self):
        self.occupant_park_time_start = 0
        self.occupant_left_parking_time_start = 0
        self.occupant_id = -1
        self.status = ParkingStatus.NOT_OCCUPIED
        self.start_datetime = 0
        self.end_datetime = 0
        self.session_id = 0

    def writeObjectIdToSharedMemory(self, object_id):
        temp_list = np.array([ord(c) for c in object_id], dtype=np.uint8)

        self.shared_memory_items[2: temp_list.shape[0] + 2] = temp_list

    def updateId(self, new_parking_id):
        self.parking_id = new_parking_id

    def updateOccupantId(self, occupant_id):
        self.occupant_id = occupant_id

    def updateCameraId(self, camera_id):
        self.camera_id = camera_id

    def updateBB(self, new_bb):
        # [TL, TR, BL, BR]
        self.bb = new_bb

    def updateStatus(self, status):
        self.status = status

    def checkAndUpdateIfConsideredParked(self, recovery_input_queue):

        if (time.time() - self.occupant_park_time_start) >= self.seconds_before_considered_parked:

            self.status = ParkingStatus.OCCUPIED
            self.shared_memory_items[1] = int(self.status.value)
            self.occupant_park_time_start = time.time()
            self.start_datetime = datetime.now()
            if self.occupant_id[0] == '?':
                send_pipe, receive_pipe = Pipe()
                recovery_input_queue.put([self.camera_id, self.ob, self.parking_id, send_pipe])

                receive_items = receive_pipe.recv()

                if receive_items[0] == ReturnStatus.SUCCESS:
                    self.occupant_id = receive_items[1]

                self.writeObjectIdToSharedMemory(self.occupant_id)
            self.session_id = Avenues.AddSession(avenue=Constants.avenue_id,
                                                 vehicle=self.occupant_id,
                                                 parking_id=self.parking_id,
                                                 start_datetime=self.start_datetime)

    def checkAndUpdateIfOccupantLeft(self):

        if self.occupant_left_parking_time_start == 0:
            self.occupant_left_parking_time_start = time.time()

        if (time.time() - self.occupant_left_parking_time_start) >= self.seconds_before_considered_left:
            t1 = Thread(target=self.chargeOccupant())
            t1.start()
            return

    def chargeOccupant(self):
        self.end_datetime = datetime.now()
        end_datetime = self.end_datetime
        start_datetime = self.start_datetime
        session_id = self.session_id
        occupant_id = self.occupant_id
        self.resetOccupant()

        print("Occupant with id " + str(occupant_id) + " will now be charged", file=sys.stderr)


        time_elapsed = end_datetime - start_datetime

        tariff_amount = int(np.ceil(time_elapsed.seconds/Constants.seconds_in_hour) * self.rate_per_hour)

        # Avenues.UpdateSession(avenue=Constants.avenue_id,
        #                       session_id=session_id,
        #                       end_datetime=end_datetime,
        #                       tariff_amount=tariff_amount)
        #
        # if Constants.sms_enabled:
        #     SMS.sendSmsToLicense(license_plate=occupant_id,
        #                          tariff_amount=tariff_amount)

    def calculateSessionTariffAmount(self, start_datetime, end_datetime, rate_per_hour):

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