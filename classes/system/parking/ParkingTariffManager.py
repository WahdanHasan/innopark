from classes.system.super_classes.TrackedObjectListener import TrackedObjectListener
from multiprocessing import Process
import sys

class ParkingTariffManager(TrackedObjectListener):
    def __init__(self, base_pool_size, new_object_in_pool_event):

        super().__init__(base_pool_size, new_object_in_pool_event)

        self.tariff_manager_process = 0
        self.should_keep_managing = True
        self.parking_spaces = []

    def Initialize(self):
        x=10

    def AddParkingSpaceToManager(self, parking_space):
        self.parking_spaces.append(parking_space)

    def StartProcess(self):
        print("[ParkingTariffManager] Starting Parking Tariff Manager.", file=sys.stderr)
        self.tariff_manager_process = Process(target=self.StartManaging)
        self.tariff_manager_process.start()

    def StopProcess(self):
        x=10

    def StartManaging(self):

        while self.should_keep_managing:
            x=10

