from classes.system.parking.ParkingTariffManager import ParkingTariffManager


def main():

    StartParkingTariffManager()


def StartParkingTariffManager():
    ptm = ParkingTariffManager()

    ptm.StartProcess()

    return ptm


if __name__ == "__main__":
    main()
