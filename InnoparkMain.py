from PyQt5.QtCore import QUrl

from classes.ui import MainScreen
from classes.system import SystemLoader
from classes.system_utilities.helper_utilities.Enums import ShutDownEvent

from PyQt5.QtWidgets import QApplication
from multiprocessing import Event
# from PyQt5.QtWebEngineWidgets import *

import sys
import time
import os

def main():

    shutdown_event = Event()
    start_system_event = Event()

    new_object_in_pool_event, detector_request_queue, tracked_object_pool_request_queue, broker_request_queue, \
    license_detector_request_queue, license_detector_queue = \
        SystemLoader.LoadComponents(shutdown_event=shutdown_event, start_system_event=start_system_event)

    app = QApplication(sys.argv)

    main_screen = MainScreen.UI(new_object_in_pool_event=new_object_in_pool_event,
                                start_system_event=start_system_event)
    main_screen.show()

    app.exec_()

    shutdown_event.set()

    tracked_object_pool_request_queue.put(ShutDownEvent.SHUTDOWN)
    detector_request_queue.put(ShutDownEvent.SHUTDOWN)
    license_detector_request_queue.put(ShutDownEvent.SHUTDOWN)
    broker_request_queue.put(ShutDownEvent.SHUTDOWN)
    license_detector_queue.put(ShutDownEvent.SHUTDOWN)

    return 0

if __name__ == "__main__":
    main()
