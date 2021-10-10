from classes.ui import MainScreen
from classes.system import SystemLoader

from PyQt5.QtWidgets import QApplication
from multiprocessing import Event
import sys

def main():

    shutdown_event = Event()
    start_system_event = Event()

    # SystemLoader.LoadComponents(shutdown_event=shutdown_event,
    #                             start_system_event=start_system_event)

    app = QApplication(sys.argv)
    main_screen = MainScreen.UI(start_system_event=start_system_event)
    main_screen.Show()

    app.exec_()

if __name__ == "__main__":
    main()
