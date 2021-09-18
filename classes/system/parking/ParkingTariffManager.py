from multiprocessing import Process

class ParkingTariffManager:
    def __init__(self):
        self.tariff_manager_process = 0
        self.should_keep_managing = True

    def Initialize(self):
        x=10

    def StartProcess(self):
        print("[ParkingTariffManager] Starting Parking Tariff Manager.")
        self.tariff_manager_process = Process(target=self.StartManaging)
        self.tariff_manager_process.start()

    def StopProcess(self):
        x=10

    def StartManaging(self):

        while self.should_keep_managing:
            x=10

