from assets.resource import logos_rc, icons_rc
from classes.system_utilities.helper_utilities import UIConstants, Constants
from classes.super_classes.FramesListener import FramesListener
from classes.super_classes.TrackedObjectListener import TrackedObjectListener
from classes.super_classes.PtmListener import PtmListener
from classes.system_utilities.image_utilities import ImageUtilities as IU

from PyQt5.QtWidgets import QMainWindow, QCheckBox, QPushButton, QWidget, QStackedWidget, QLabel, QHBoxLayout
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPixmap, QImage
from PyQt5 import uic
from threading import Thread
from multiprocessing import shared_memory
import numpy as np
import sys
import time

class UI(QMainWindow):
    def __init__(self, new_object_in_pool_event, start_system_event):
        QMainWindow.__init__(self)

        uic.loadUi("assets\\ui\\MainScreen.ui", self)

        self.debug_ot_cb = self.findChild(QCheckBox, "debugOtCb")
        self.debug_ptm_cb = self.findChild(QCheckBox, "debugPtmCb")
        self.start_system_button = self.findChild(QPushButton, "startSystemButton")
        self.menu_button = self.findChild(QPushButton, "menuButton")
        self.left_slide_menu = self.findChild(QWidget, "leftSlideMenu")
        self.dashboard_page_button = self.findChild(QPushButton, "dashboardButton")
        self.setup_page_button = self.findChild(QPushButton, "setupButton")
        self.debug_page_button = self.findChild(QPushButton, "debugButton")
        self.dashboard_page = self.findChild(QWidget, "dashboardPage")
        self.setup_page = self.findChild(QWidget, "setupPage")
        self.debug_page = self.findChild(QWidget, "debugPage")
        self.screen_stacked_widget = self.findChild(QStackedWidget, "screenStackedWidget")
        self.debug_frames_layout = self.findChild(QHBoxLayout, "debugFrames")
        self.menu_label = self.findChild(QLabel, "screenPageLabel")

        self.start_system_button.clicked.connect(self.startSystemButtonOnClick)
        self.menu_button.clicked.connect(self.menuButtonOnClick)
        self.dashboard_page_button.clicked.connect(self.dashboardButtonOnClick)
        self.setup_page_button.clicked.connect(self.setupButtonOnClick)
        self.debug_page_button.clicked.connect(self.debugButtonOnClick)

        self.start_system_event = start_system_event
        self.new_object_in_pool_event = new_object_in_pool_event

        self.amount_of_trackers = len(Constants.CAMERA_DETAILS)
        self.amount_of_frames_in_shared_memory = self.amount_of_trackers + len(Constants.ENTRANCE_CAMERA_DETAILS)

        self.frames_listener = FramesListener()
        self.tracked_object_listener = TrackedObjectListener(amount_of_trackers=self.amount_of_trackers,
                                                             new_object_in_pool_event=new_object_in_pool_event)
        self.ptm_listener = PtmListener()

        self.debug_frame_labels = []
        self.left_slide_menu_min_width = 0
        self.left_slide_menu_max_width = 200

        self.debug_update_thread = 0
        self.should_keep_updating_debug = True
        self.is_debug_screen_active = False
        self.frame_offset_length = len(Constants.ENTRANCE_CAMERA_DETAILS)

        self.menu_buttons = [self.dashboard_page_button, self.setup_page_button, self.debug_page_button]

        self.onLoad()

    def onLoad(self):
        self.left_slide_menu.setMaximumWidth(self.left_slide_menu_min_width)
        self.dashboardButtonOnClick()

        self.initializeDebugFrames()

        self.launchDebugUpdaterThread()

    def initializeDebugFrames(self):

        for i in range(self.amount_of_frames_in_shared_memory):
            temp_label = QLabel("test", self)

            # temp_frame = self.frames_listener.getFrameByCameraId(i)
            # temp_height, temp_width, temp_channel = temp_frame.shape
            # temp_bytes_per_line = 3 * temp_width
            # temp_q_img = QImage(temp_frame.data, temp_width, temp_height, temp_bytes_per_line, QImage.Format_RGB888)
            # temp_label.setPixmap(QPixmap(temp_q_img))

            temp_label.setMaximumWidth(300)
            temp_label.setMaximumHeight(300)
            temp_label.setScaledContents(True)
            self.debug_frames_layout.addWidget(temp_label)
            self.debug_frame_labels.append(temp_label)

    def launchDebugUpdaterThread(self):
        self.debug_update_thread = Thread(target=self.updateDebugScreen)
        self.debug_update_thread.daemon = True
        self.debug_update_thread.start()

    def startSystemButtonOnClick(self):
        print("[GUI][Dashboard] Starting system", file=sys.stderr)

        self.start_system_event.set()

    def menuButtonOnClick(self):
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

    def dashboardButtonOnClick(self):
        self.screen_stacked_widget.setCurrentWidget(self.dashboard_page)
        self.resetAllMenuButtonColors()

        self.dashboard_page_button.setStyleSheet("background-color:" + UIConstants.menu_button_color)
        self.menu_label.setText("Dashboard")

    def setupButtonOnClick(self):
        self.screen_stacked_widget.setCurrentWidget(self.setup_page)
        self.resetAllMenuButtonColors()

        self.setup_page_button.setStyleSheet("background-color:" + UIConstants.menu_button_color)
        self.menu_label.setText("Setup")

    def debugButtonOnClick(self):
        self.screen_stacked_widget.setCurrentWidget(self.debug_page)
        self.resetAllMenuButtonColors()

        self.debug_page_button.setStyleSheet("background-color:" + UIConstants.menu_button_color)
        self.menu_label.setText("Debug")

        self.is_debug_screen_active = True

    def resetAllMenuButtonColors(self):
        for i in range(len(self.menu_buttons)):
            self.menu_buttons[i].setStyleSheet("background-color:transparent;")

        self.is_debug_screen_active = False

    def updateDebugScreen(self):
        import cv2

        self.frames_listener.initialize()
        self.tracked_object_listener.initialize()
        self.ptm_listener.initialize()

        while self.should_keep_updating_debug:
            if self.is_debug_screen_active:
                ids, bbs = self.tracked_object_listener.getAllActiveTrackedProcessItems()
                for i in range(self.amount_of_frames_in_shared_memory):

                    temp_frame = self.frames_listener.getFrameByCameraId(camera_id=i).copy()

                    if i >= (self.amount_of_frames_in_shared_memory - self.amount_of_trackers):
                        if self.debug_ot_cb.checkState():
                            if ids is not None and bbs is not None:
                                temp_active_ids = []
                                temp_active_bbs = []
                                for j in range(len(bbs)):
                                    if ids[1][j] == i:
                                        temp_active_bbs.append(bbs[j])
                                        temp_active_ids.append(ids[2][j])

                                temp_frame = IU.DrawBoundingBoxAndClasses(image=temp_frame,
                                                                          class_names=temp_active_ids,
                                                                          bounding_boxes=temp_active_bbs)
                        if self.debug_ptm_cb.checkState():
                            temp_frame = cv2.add(temp_frame, self.ptm_listener.getFrameByCameraId(i - self.frame_offset_length))



                    temp_height, temp_width, temp_channel = temp_frame.shape
                    temp_bytes_per_line = 3 * temp_width
                    temp_frame = cv2.cvtColor(temp_frame, cv2.COLOR_BGR2RGB)
                    temp_q_img = QImage(temp_frame.data, temp_width, temp_height, temp_bytes_per_line, QImage.Format_RGB888)
                    self.debug_frame_labels[i].setPixmap(QPixmap(temp_q_img))

            time.sleep(UIConstants.debug_refresh_rate)

