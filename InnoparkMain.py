from classes.ui import MainScreen
from classes.system import SystemLoader

from PyQt5.QtWidgets import QApplication
from multiprocessing import Event
import sys

def main():

    shutdown_event = Event()
    start_system_event = Event()

    SystemLoader.LoadComponents(shutdown_event=shutdown_event,
                                start_system_event=start_system_event)

    app = QApplication(sys.argv)
    main_screen = MainScreen.UI()
    main_screen.Show()


    start_system_event.set()


    app.exec_()

if __name__ == "__main__":
    main()
