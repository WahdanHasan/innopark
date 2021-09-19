from classes.system_utilities.helper_utilities.Enums import ParkingStatus

class ParkingSpace:
    def __init__(self):
        self.parking_id = -1
        self.occupant_id = -1
        self.camera_id = -1
        self.bb = []
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

