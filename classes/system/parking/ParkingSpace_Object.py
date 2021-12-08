class ParkingSpace_Object:
    def __init__(self, internal_id, is_occupied, camera_id, parking_id, parking_type, rate_per_hour, bounding_box, occupancy_box):
        # DB initialized variables
        self.internal_id = internal_id
        self.is_occupied = is_occupied
        self.camera_id = camera_id
        self.parking_id = parking_id
        self.bounding_box = bounding_box
        self.occupancy_box = occupancy_box
        self.parking_type = parking_type
        self.rate_per_hour = rate_per_hour


    def __iter__(self):
        yield 'internal_id', self.internal_id
        yield 'is_occupied', self.is_occupied
        yield 'camera_id', self.camera_id
        yield 'parking_id', self.parking_id
        yield 'parking_type', self.parking_type
        yield 'rate_per_hour', self.rate_per_hour
        yield 'bounding_box', self.bounding_box
        yield 'occupancy_box', self.occupancy_box


