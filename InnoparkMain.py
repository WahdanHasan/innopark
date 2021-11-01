from classes.ui import MainScreen
from classes.system import SystemLoader

from PyQt5.QtWidgets import QApplication
from multiprocessing import Event
import sys

def main():

    shutdown_event = Event()
    start_system_event = Event()

    new_object_in_pool_event = SystemLoader.LoadComponents(shutdown_event=shutdown_event,
                                                           start_system_event=start_system_event)

    app = QApplication(sys.argv)

    main_screen = MainScreen.UI(new_object_in_pool_event=new_object_in_pool_event,
                                start_system_event=start_system_event)
    main_screen.show()

    app.exec_()

if __name__ == "__main__":
    main()
