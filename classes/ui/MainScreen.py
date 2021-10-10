from assets.resource import logos_rc, icons_rc

from PyQt5.QtWidgets import QMainWindow, QCheckBox, QPushButton, QWidget
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve
from PyQt5 import uic
import sys

class UI(QMainWindow):
    def __init__(self, start_system_event):
        super(UI, self).__init__()

        uic.loadUi("assets\\ui\\MainScreen.ui", self)

        self.debug_ot_cb = self.findChild(QCheckBox, "debugOtCb")
        self.debug_ptm_cb = self.findChild(QCheckBox, "debugPtmCb")
        self.start_system_button = self.findChild(QPushButton, "startSystemButton")
        self.menu_button = self.findChild(QPushButton, "menuButton")
        self.left_slide_menu = self.findChild(QWidget, "leftSlideMenu")

        self.start_system_button.clicked.connect(self.StartSystemButtonOnClick)
        self.menu_button.clicked.connect(self.MenuButtonOnClick)

        self.start_system_event = start_system_event

        self.left_slide_menu_min_width = 0
        self.left_slide_menu_max_width = 200


        self.OnLoad()

    def OnLoad(self):
        self.left_slide_menu.setMaximumWidth(self.left_slide_menu_min_width)

    def Show(self):
        self.show()

    def StartSystemButtonOnClick(self):
        print("[GUI][Dashboard] Starting system", file=sys.stderr)

        self.start_system_event.set()

    def MenuButtonOnClick(self):
        width = self.left_slide_menu.width()

        if width == self.left_slide_menu_min_width:
            self.animation = QPropertyAnimation(self.left_slide_menu, b"minimumWidth")
            self.animation.setDuration(400)
            self.animation.setStartValue(self.left_slide_menu_min_width)
            self.animation.setEndValue(self.left_slide_menu_max_width)
            self.animation.setEasingCurve(QEasingCurve.InOutQuart)
            self.animation.start()
        elif width == self.left_slide_menu_max_width:
            self.animation = QPropertyAnimation(self.left_slide_menu, b"minimumWidth")
            self.animation.setDuration(400)
            self.animation.setStartValue(self.left_slide_menu_max_width)
            self.animation.setEndValue(self.left_slide_menu_min_width)
            self.animation.setEasingCurve(QEasingCurve.InOutQuart)
            self.animation.start()
