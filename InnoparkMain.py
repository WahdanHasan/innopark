from classes.ui import MainScreen
from classes.system import SystemLoader

from PyQt5.QtWidgets import QApplication
from multiprocessing import Event
import sys

def main():

    shutdown_event = Event()

    # ProgramLoader.LoadComponents(shutdown_event=shutdown_event)

    app = QApplication(sys.argv)
    main_screen = MainScreen.UI()
    main_screen.Show()

    app.exec_()

if __name__ == "__main__":
    main()
