from classes.system.super_classes.TrackedObjectListener import TrackedObjectListener
from classes.system.parking.ParkingSpace import ParkingSpace
from classes.system_utilities.helper_utilities import Constants
import json

from multiprocessing import Process
import sys


class ParkingTariffManager(TrackedObjectListener):
    def __init__(self, base_pool_size, new_object_in_pool_event):

        super().__init__(base_pool_size, new_object_in_pool_event)

        self.tariff_manager_process = 0
        self.should_keep_managing = True
        self.parking_spaces = []

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
            x=10

