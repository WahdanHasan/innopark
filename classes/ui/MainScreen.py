from PyQt5.QtWidgets import QMainWindow, QCheckBox
from PyQt5 import uic
import sys

class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()

        uic.loadUi("assets\\ui\\MainScreen.ui", self)

        self.debug_ot_cb = self.findChild(QCheckBox, "debugOtCb")
        self.debug_ptm_cb = self.findChild(QCheckBox, "debugPtmCb")

    def Show(self):
        self.show()





# app = QApplication(sys.argv)
# UIWindow = UI()
#
# app.exec_()
