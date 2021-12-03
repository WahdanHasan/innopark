import datetime

from assets.resource import logos_rc, icons_rc
from classes.system_utilities.helper_utilities import UIConstants, Constants
from classes.super_classes.FramesListener import FramesListener
from classes.super_classes.TrackedObjectListener import TrackedObjectListener
from classes.super_classes.PtmListener import PtmListener
from classes.system_utilities.image_utilities import ImageUtilities as IU
from classes.system_utilities.data_utilities.Avenues import GetFinesFromDb

from PyQt5.QtWidgets import QMainWindow, QCheckBox, QPushButton, QWidget, QStackedWidget, QLabel, QHBoxLayout, QDialog, \
    QLineEdit, QStyle, QSlider, QVBoxLayout, QSizePolicy, QFileDialog, QGraphicsScene, QGraphicsView
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, Qt, QUrl, QSizeF
from PyQt5.QtGui import QPixmap, QImage, QColor
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget, QGraphicsVideoItem
from PyQt5.QtWebEngineWidgets import *
import webbrowser

from classes.system_utilities.data_utilities.DatabaseUtilities import UpdateDataTwoFields, UpdateData

import urllib

from PyQt5 import uic
from threading import Thread
from multiprocessing import shared_memory
import numpy as np
import sys
import time
from datetime import datetime

class UI(QMainWindow):
    def __init__(self, new_object_in_pool_event, start_system_event):
        QMainWindow.__init__(self)

        uic.loadUi("assets\\ui\\MainScreen.ui", self)

        self.debug_ot_cb = self.findChild(QCheckBox, "debugOtCb")
        self.debug_ptm_cb = self.findChild(QCheckBox, "debugPtmCb")
        self.debug_pvm_cb = self.findChild(QCheckBox, "debugPvmCb")
        self.start_system_button = self.findChild(QPushButton, "startSystemButton")
        self.menu_button = self.findChild(QPushButton, "menuButton")
        self.left_slide_menu = self.findChild(QWidget, "leftSlideMenu")
        self.dashboard_page_button = self.findChild(QPushButton, "dashboardButton")
        self.setup_page_button = self.findChild(QPushButton, "setupButton")
        self.violation_review_page_button = self.findChild(QPushButton, "violationReviewButton")
        self.debug_page_button = self.findChild(QPushButton, "debugButton")
        self.dashboard_page = self.findChild(QWidget, "dashboardPage")
        self.setup_page = self.findChild(QWidget, "setupPage")
        self.debug_page = self.findChild(QWidget, "debugPage")
        self.violation_review_page = self.findChild(QWidget, "violationReviewPage")
        self.screen_stacked_widget = self.findChild(QStackedWidget, "screenStackedWidget")
        self.debug_frames_layout = self.findChild(QHBoxLayout, "debugFrames")
        self.menu_label = self.findChild(QLabel, "screenPageLabel")
        self.review_fines_table_widget = self.findChild(QTableWidget, "tableWidget")
        self.violation_refresh_button = self.findChild(QPushButton, "violationRefreshButton")
        self.violation_review_fine_button = QPushButton("Review")

        self.start_system_button.clicked.connect(self.startSystemButtonOnClick)
        self.menu_button.clicked.connect(self.menuButtonOnClick)
        self.dashboard_page_button.clicked.connect(self.dashboardButtonOnClick)
        self.setup_page_button.clicked.connect(self.setupButtonOnClick)
        self.violation_review_page_button.clicked.connect(self.violationReviewButtonOnClick)
        self.debug_page_button.clicked.connect(self.debugButtonOnClick)

        self.violation_refresh_button.clicked.connect(self.loadReviewFinesFromDb)
        # self.violation_review_fine_button.clicked.connect(self.reviewButtonOnClick)
        self.fines_id = []
        self.fines_data = []

        self.start_system_event = start_system_event
        self.new_object_in_pool_event = new_object_in_pool_event

        self.amount_of_trackers = len(Constants.CAMERA_DETAILS)
        self.amount_of_frames_in_shared_memory = self.amount_of_trackers + len(Constants.ENTRANCE_CAMERA_DETAILS)

        self.frames_listener = FramesListener()
        self.tracked_object_listener = TrackedObjectListener(amount_of_trackers=self.amount_of_trackers,
                                                             new_object_in_pool_event=new_object_in_pool_event)
        self.ptm_listener = PtmListener()

        # self.pvm_listener = PvmListener()


        self.debug_frame_labels = []
        self.left_slide_menu_min_width = 0
        self.left_slide_menu_max_width = 200

        self.debug_update_thread = 0
        self.should_keep_updating_debug = True
        self.is_debug_screen_active = False
        self.frame_offset_length = len(Constants.ENTRANCE_CAMERA_DETAILS)

        self.menu_buttons = [self.dashboard_page_button, self.setup_page_button, self.debug_page_button,
                             self.violation_review_page_button]

        self.review_fines_columns = [Constants.fine_type_key, Constants.vehicle_key,
                                Constants.created_datetime_key, Constants.due_datetime_key, Constants.footage_key]

        self.onLoad()

    def onLoad(self):
        self.left_slide_menu.setMaximumWidth(self.left_slide_menu_min_width)
        self.dashboardButtonOnClick()

        self.initializeDebugFrames()

        self.launchDebugUpdaterThread()

        # load data from the db
        self.loadReviewFinesFromDb()

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
        self.is_debug_screen_active = False
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

        self.is_debug_screen_active = True

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

    def violationReviewButtonOnClick(self):
        self.screen_stacked_widget.setCurrentWidget(self.violation_review_page)
        self.resetAllMenuButtonColors()

        self.violation_review_page_button.setStyleSheet("background-color:" + UIConstants.menu_button_color)
        self.menu_label.setText("Violation Review")

    def loadReviewFinesFromDb(self):
        print("coming in")
        # fines = [{self.review_fines_columns[0]:Constants.fine_type_double_parking, self.review_fines_columns[1]:"J71612",
        #           self.review_fines_columns[2]:"29/11/2021", self.review_fines_columns[3]:"25/11/2021"},
        #          {
        #              self.review_fines_columns[0]: Constants.fine_type_double_parking,
        #              self.review_fines_columns[1]: "A12345",
        #              self.review_fines_columns[2]: "30/12/2021", self.review_fines_columns[3]: "05/02/2022"
        #          }]
        #
        # for i in range (30):
        #     fines.append({self.review_fines_columns[0]:Constants.fine_type_double_parking, self.review_fines_columns[1]:"J71612",
        #           self.review_fines_columns[2]:"29/11/2021", self.review_fines_columns[3]:"25/11/2021"})

        self.fines_id, self.fines_data = GetFinesFromDb(Constants.avenue_id)

        if self.fines_id is None or not self.fines_id:
            # set the number of rows to one
            self.review_fines_table_widget.setRowCount(1)

            # set row and column (0,0) to the below
            self.review_fines_table_widget.setItem(0, 0, QTableWidgetItem("No fines available to review"))
            self.review_fines_table_widget.item(0,0).setForeground(QColor(255, 0, 0))

            # resize the column index 0
            self.review_fines_table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            return

        extracted_fines_length = len(self.fines_id)
        # don't consider the url (last index) as part of column length so it is not displayed
        column_length = len(self.review_fines_columns)-1

        # set the number of rows to the length of extracted fines
        self.review_fines_table_widget.setRowCount(extracted_fines_length)

        # display the fines info on the system screen
        resize_column = True
        for row in range(extracted_fines_length):
            for column in range(column_length):

                fine_data_key = self.review_fines_columns[column]
                fine_data_value = self.fines_data[row][self.review_fines_columns[column]]

                # if datetime then convert datetime object to string
                # and resize column only on first iteration
                if "datetime" in fine_data_key:
                    local_datetime = datetime.combine(date=fine_data_value.date(), time=fine_data_value.time(), tzinfo=Constants.local_timezone)

                    fine_data_value = datetime.strftime(local_datetime, '%Y-%m-%d %H:%M:%S')

                    if resize_column:
                        self.review_fines_table_widget.horizontalHeader().setSectionResizeMode(column, QHeaderView.Stretch)

                self.review_fines_table_widget.setItem(row, column, QTableWidgetItem(str(fine_data_value)))
            resize_column = False

            # add a review button
            self.review_fines_table_widget.setCellWidget(row, column_length, self.violation_review_fine_button)
            self.violation_review_fine_button.clicked.connect(lambda: self.reviewButtonOnClick(row))

        # self.review_fines_table_widget.horizontalHeader().setStretchLastSection(True)
        # self.review_fines_table_widget.horizontalHeader().setSectionResizeMode(
        #     QHeaderView.Stretch)

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
            try:
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

                            # if self.debug_pvm_cb.checkState():
                            #     temp_frame = cv2.add(temp_frame, self.pvm_listener.getFrameByCameraId(i - self.frame_offset_length))


                        temp_height, temp_width, temp_channel = temp_frame.shape
                        temp_bytes_per_line = 3 * temp_width
                        temp_frame = cv2.cvtColor(temp_frame, cv2.COLOR_BGR2RGB)
                        temp_q_img = QImage(temp_frame.data, temp_width, temp_height, temp_bytes_per_line, QImage.Format_RGB888)
                        if self.is_debug_screen_active:
                            self.debug_frame_labels[i].setPixmap(QPixmap(temp_q_img))

                time.sleep(UIConstants.debug_refresh_rate)
            except:
                x=10

    def reviewButtonOnClick(self, row):
        # get fine data of the button row
        fine_id = self.fines_id[row]
        vehicle = self.fines_data[row][Constants.vehicle_key]
        fine_type = self.fines_data[row][Constants.fine_type_key]
        footage_url = self.fines_data[row][Constants.footage_key]

        # execute the review fine ui page
        review_fine_ui = ReviewFineUI(fine_id=fine_id, vehicle=vehicle, fine_type=fine_type, footage_url=footage_url)
        review_fine_ui.setWindowFlags(Qt.WindowCloseButtonHint)
        review_fine_ui.exec_()

class ReviewFineUI(QDialog):
    def __init__(self, fine_id, vehicle, fine_type, footage_url):
        QDialog.__init__(self)
        uic.loadUi("assets\\ui\\ReviewFineScreen.ui", self)

        self.fine_id = fine_id
        self.url = footage_url

        # display the fine details
        self.vehicle_line_edit = self.findChild(QLineEdit, "vehicleLineEdit").setText(vehicle)
        self.fine_type_line_edit = self.findChild(QLineEdit, "fineTypeLineEdit").setText(fine_type)

        # get the buttons
        self.view_footage_button = self.findChild(QPushButton, "viewFootageButton")
        self.view_footage_button.clicked.connect(self.open_footage_in_browser)

        self.accept_fine_button = self.findChild(QPushButton, "acceptFineButton")
        self.accept_fine_button.clicked.connect(lambda: self.updateFine(fine_is_accepted=True, fine_is_reviewed=True))

        self.decline_fine_button = self.findChild(QPushButton, "declineFineButton")
        self.decline_fine_button.clicked.connect(lambda: self.updateFine(fine_is_accepted=False, fine_is_reviewed=True))

        self.error_label = self.findChild(QLabel, "errorLabel")

    def updateFine(self, fine_is_accepted, fine_is_reviewed):
        if fine_is_accepted:
            print("fine is accepted")
            UpdateDataTwoFields(collection=Constants.avenues_collection_name+"/"+Constants.avenue_id+"/"+Constants.fines_info_subcollection_name,
                                document=self.fine_id, field_to_edit1=Constants.is_accepted_key, new_data1=fine_is_accepted,
                                field_to_edit2=Constants.is_reviewed_key, new_data2=fine_is_reviewed)
        else:
            print("fine is declined")
            # only update the is_reviewed field because is_accepted is originally false
            UpdateData(collection=Constants.avenues_collection_name+"/"+Constants.avenue_id+"/"+Constants.fines_info_subcollection_name,
                       document=self.fine_id, field_to_edit=Constants.is_reviewed_key, new_data=fine_is_reviewed)

        print("closing dialog")
        self.close_dialog()

    def close_dialog(self):
        self.close()


    def open_footage_in_browser(self):
        if not self.url or self.url == "":
            self.error_label.setText("ERROR: No footage available")
            return
        webbrowser.open(self.url)