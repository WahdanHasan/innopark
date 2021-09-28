from classes.system_utilities.helper_utilities.Enums import ParkingStatus

from twilio.rest import Client
import sys
import time

class ParkingSpace:
    def __init__(self, camera_id, parking_id, bounding_box, seconds_before_considered_parked=2, seconds_before_considered_left=2):
        # JSON initialized variables
        self.camera_id = camera_id
        self.parking_id = parking_id
        self.bb = [
                    [bounding_box['top_left_x'], bounding_box['top_left_y']],
                    [bounding_box['top_right_x'], bounding_box['top_right_y']],
                    [bounding_box['bottom_left_x'], bounding_box['bottom_left_y']],
                    [bounding_box['bottom_right_x'], bounding_box['bottom_right_y']]
                  ]

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

        # Find your Account SID and Auth Token at twilio.com/console
        # and set the environment variables. See http://twil.io/secure
        # account_sid = 'ACee57670a80d4352d8c0623ec6fa1beac'
        # auth_token = 'a7c690d1d4d857388692925166f0072a'
        # twilio_number = '+447401068297'
        # my_number = '+971502398737'
        # client = Client(account_sid, auth_token)
        #
        # message = client.messages.create(body='InnoPark: Vehicle with license ' + str(self.occupant_id) + ' will now be charged 50000.00AED\n Reply \'InnoPark is geh\' to refute payment',
        #                                  from_=twilio_number,
        #                                  to=my_number
        #                                  )
        #
        # print(message.sid)






