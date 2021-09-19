from classes.system_utilities.helper_utilities.Enums import ParkingStatus

class ParkingSpace:
    def __init__(self, camera_id, parking_id, bounding_box):
        self.camera_id = camera_id
        self.parking_id = parking_id
        self.bb = [
                    [bounding_box['top_left_x'], bounding_box['top_left_y']],
                    [bounding_box['top_right_x'], bounding_box['top_right_y']],
                    [bounding_box['bottom_left_x'], bounding_box['bottom_left_y']],
                    [bounding_box['bottom_right_x'], bounding_box['bottom_right_y']]
                  ]

        self.occupant_id = -1
        self.status = ParkingStatus.NOT_OCCUPIED.value

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

    def GetId(self):
        return self.parking_id

    def GetOccupantId(self):
        return self.occupant_id

    def GetCameraId(self):
        return self.camera_id

    def GetBB(self):
        return self.bb

    def GetStatus(self):
        return self.status

    def doSomething(self):
        print(str(self.camera_id) + " " + str(self.parking_id) + " ")
        print(self.bb)
