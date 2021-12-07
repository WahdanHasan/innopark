from classes.super_classes.TrackedObjectListener import TrackedObjectListener
from classes.system.parking.ParkingSpace import ParkingSpace
from classes.system_utilities.helper_utilities import Constants
# from classes.system_utilities.helper_utilities.Enums import ParkingStatus, YoloModel
from classes.system_utilities.helper_utilities.Enums import ParkingStatus
from classes.system_utilities.image_utilities import ImageUtilities as IU
from classes.system_utilities.helper_utilities.Enums import ImageResolution
import classes.system_utilities.data_utilities.DatabaseUtilities as DU
from datetime import datetime, timezone

from classes.system_utilities.data_utilities.Avenues import AddFine, GetSessionsDueToday

from classes.super_classes.PtmListener import PtmListener
from multiprocessing import Process, shared_memory
import numpy as np
import cv2
import sys
import json
import time, logging
import math
import threading


class ParkingViolationManager(TrackedObjectListener, PtmListener):

    def __init__(self, amount_of_trackers, new_object_in_pool_event, shutdown_event, start_system_event, pvm_initialized_event):

        TrackedObjectListener.__init__(self, amount_of_trackers, new_object_in_pool_event)
        PtmListener.__init__(self)

        self.shutdown_event = shutdown_event
        self.start_system_event = start_system_event
        self.pvm_initialized_event = pvm_initialized_event
        self.violation_manager_process = 0
        self.should_keep_managing = True
        self.base_blank = np.zeros(
                                    shape=(Constants.default_camera_shape[1], Constants.default_camera_shape[0], Constants.default_camera_shape[2]),
                                    dtype=np.uint8
        )

        # camera_id, parking_id, parking_bbs, parking_status
        # TL, TR, BL, BR
        self.parking_spaces = [
            [
                                3,
                                188,
                                [[349, 214],
                                [481, 214],
                                [480, 391],
                                [718, 367]],
                                False
             ]
        ]

        self.camera_id_key = "camera_id_"
        self.parking_status_key = "parking_status"
        self.license_detected_key = "license_detected_status"
        self.license_detected = True
        self.license_notDetected = False

        self.minimum_length_of_vehicle_trail = 0

        # self.maximum_tracked_vehicle_bbs = 100

        self.camera_offset = len(Constants.ENTRANCE_CAMERA_DETAILS)

        self.latest_tracked_vehicle_bbs = {}

        self.should_build_vehicle_bb_history = True

        # Variables for Violation Type "Exceeding Due Date"
        self.time_interval_to_check_violation = 60 # in seconds
        self.today_start_date = None
        self.today_end_date = None

        self.sessions_due_today_ids = []
        self.sessions_due_today_data = []

        # for i in range(len(Constants.CAMERA_DETAILS)):
        #     self.latest_tracked_vehicle_frames.append([None]*self.maximum_tracked_vehicle_frame_history)

        self.is_debug_mode = True
        self.frame_shms = []
        self.frames = []

        self.temp_counter = 0
        self.threshold_percentage = 0.75

        self.thread_check_due_dates = 0
        self.segmentation_model = 0

    def createSharedMemoryStuff(self, amount_of_trackers):
        for i in range(amount_of_trackers):
            temp_shm = shared_memory.SharedMemory(create=True,
                                                  name=Constants.parking_violation_management_shared_memory_prefix + str(i),
                                                  size=self.base_blank.nbytes)

            temp_frame = np.ndarray(self.base_blank.shape, dtype=np.uint8, buffer=temp_shm.buf)
            self.frame_shms.append(temp_shm)
            self.frames.append(temp_frame)

    def startProcess(self):
        print("[ParkingViolationManager] Starting Parking Violation Manager.", file=sys.stderr)
        self.violation_manager_process = Process(target=self.startManaging)
        self.violation_manager_process.start()

    def stopProcess(self):
        self.thread_check_due_dates.join()
        self.tariff_manager_process.terminate()

    def checkForViolationTypeExceedingDueDateEvery(self, seconds_to_delay):
        while True:
            time.sleep(seconds_to_delay)
            try:
                if len(self.sessions_due_today_ids) <=0:
                    logging.critical(" - Will stop checking for violation type 'Exceeded Due Dates'.")
                    return

                self.checkDueDateComparedToNow()
            except Exception:
                logging.exception("Couldn't execute the thread task")

    def checkDueDateComparedToNow(self):
        now_datetime = datetime.now(timezone.utc)
        # print("now time to be compared to due date: ", now, file=sys.stderr)
        # print(self.sessions_due_today_data, file=sys.stderr)


        for i in range(len(self.sessions_due_today_ids)):

            # print("due date being compared: ", self.sessions_due_today_data[i][Constants.due_datetime_key])

            # check if now exceeds due datetime
            # if it does, record a fine in the db
            if self.sessions_due_today_data[i][Constants.due_datetime_key] > now_datetime:
                break

            AddFine(avenue=Constants.avenue_id,
                      avenue_name=self.sessions_due_today_data[i]["avenue_name"],
                      session_id=self.sessions_due_today_ids[i],
                      vehicle=self.sessions_due_today_data[i]["vehicle"],
                      fine_type=Constants.fine_type_exceeded_due_date)


            # pop the sessions that are fined
            self.sessions_due_today_ids.pop(i)
            self.sessions_due_today_data.pop(i)

    def startManaging(self):
        TrackedObjectListener.initialize(self)
        PtmListener.initialize(self)

        # initialize thread that checks sessions' due datetime compared to now datetime.
        # if now datetime is past due date, then add a record of the fine with type "Exceeded Due Date"
        # if it doesn't yet exist in db
        self.thread_check_due_dates = threading.Thread(
            target=lambda: self.checkForViolationTypeExceedingDueDateEvery(self.time_interval_to_check_violation))

        self.createSharedMemoryStuff(self.amount_of_trackers)

        # from classes.system_utilities.image_utilities import ObjectDetection as LicenseDetector
        #
        # LicenseDetector.OnLoad(model=YoloModel.LICENSE_DETECTOR)

        # load mask rcnn
        self.loadMaskRCNNModel()

        self.pvm_initialized_event.set()
        self.start_system_event.wait()

        # set the start and end datetimes of today in UTC
        self.setTodayStartEndDate()

        self.sessions_due_today_ids, self.sessions_due_today_data = GetSessionsDueToday(
                                                      collection=Constants.avenues_collection_name+"/"+Constants.avenue_id+"/"+Constants.sessions_info_subcollection_name,
                                                      today_start_datetime=self.today_start_date,
                                                      today_end_datetime=self.today_end_date)

        # if there exists sessions due today, start the thread.
        if self.sessions_due_today_ids is not None:
            print("session ids today: ", self.sessions_due_today_ids, file=sys.stderr)
            self.thread_check_due_dates.start()

        while self.should_keep_managing:

            parking_ids, parking_occupants = self.getOccupiedParkingSpaceItems()

            # vehicle_ids, vehicle_bbs = self.getAllActiveTrackedProcessItems()

            # if parking_ids or parking_ids is not None:
            #     print("parking_ids: ", parking_ids, file=sys.stderr)
            #     print("paring_occupants: ", parking_occupants, file=sys.stderr)

            # don't proceed there are no parkings occupied
            # if not parking_ids or parking_ids is None:
            #     return

            self.checkAndUpdateViolationStatuses(parking_ids=parking_ids,
                                                 parking_occupants=parking_occupants)

            # if self.is_debug_mode:
            #     self.writeDebugItems()

            time.sleep(0.033)

    def checkAndUpdateViolationStatuses(self, parking_ids, parking_occupants):
        result = self.segmentation_model.segmentAsPascalvoc("./data/reference footage/images/car_parked3_new_cropped.jpg")
        mask = result[1]

        cv2.imshow("mask", mask)
        cv2.waitKey(0)

        result = self.segmentation_model.segmentAsPascalvoc(
            "./data/reference footage/images/car_parked3_new_cropped.jpg")
        mask = result[1]
        cv2.imshow("mask2", mask)
        cv2.waitKey(0)

        print("checking and updating violation statuses", file=sys.stderr)


    def loadMaskRCNNModel(self):
        from pixellib.semantic import semantic_segmentation
        self.segmentation_model = semantic_segmentation()

        self.segmentation_model.load_pascalvoc_model(
            "./config/maskrcnn/deeplabv3_xception_tf_dim_ordering_tf_kernels.h5")

        result = self.segmentation_model.segmentAsPascalvoc(
            "./data/reference footage/images/car_parked3_new_cropped.jpg")

        # self.segmentation_model.segmentFrameAsPascalvoc(np.zeros(shape=(
        #     Constants.default_camera_shape[1], Constants.default_camera_shape[0], Constants.default_camera_shape[2]),
        #     dtype=np.uint8))


    def setTodayStartEndDate(self):
        # set the start of today in UTC time 08:00 PM previous day
        today = datetime.now().astimezone() # get uae time now

        today_start = datetime(today.year, today.month, today.day, tzinfo=today.tzinfo) # set to uae time 12:00:00 AM of today

        today_start = today_start.astimezone(timezone.utc) # convert uae time 12:00:00 AM to UTC time 8:00:00 PM previous day

        today_end = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=today.tzinfo)  # set to uae time 11:59:59 PM of today

        today_end = today_end.astimezone(timezone.utc)  # convert uae time 11:59:59 AM to UTC time 8:59:59 AM previous day

        self.today_start_date = today_start
        self.today_end_date = today_end














    def FcheckAndUpdateViolationStatuses(self, parking_ids, vehicle_ids, vehicle_bbs, license_detector):
        # don't check for violation if there are not parkings occupied
        if not parking_ids or parking_ids is None:
            return

        # An object tracker cannot be on the id 0
        if not vehicle_ids or vehicle_ids is None:
            return

        if not vehicle_bbs or vehicle_bbs is None:
            return

        for i in range(len(vehicle_bbs)):
            self.temp_counter +=1
            license_plate = vehicle_ids[2][i]
            camera_id = vehicle_ids[1][i]

            # Initialize license_plate dict for new vehicle
            if license_plate not in self.latest_tracked_vehicle_bbs:
                # initialize the parking status
                self.latest_tracked_vehicle_bbs[license_plate] = {
                    self.parking_status_key: ParkingStatus.NOT_OCCUPIED,
                    self.license_detected_key: self.license_notDetected
                }

                # initialize a list for each camera
                for camera_details in Constants.CAMERA_DETAILS:
                    self.latest_tracked_vehicle_bbs[license_plate][self.camera_id_key+str(camera_details[0])] = []

            # Build the history of vehicle bbs if vehicle is not parked
            if self.latest_tracked_vehicle_bbs[license_plate][self.parking_status_key] == ParkingStatus.NOT_OCCUPIED:
                self.buildVehicleBbHistory(bbs=vehicle_bbs, camera_id=camera_id, vehicle_plate=license_plate)

            for j in range(len(self.parking_spaces)):
                # if camera_id != self.parking_spaces[j].camera_id:
                if camera_id != self.parking_spaces[j][0]:
                    continue

                # if self.parking_spaces.status == ParkingStatus.OCCUPIED:
                if self.parking_spaces[j][3] == ParkingStatus.OCCUPIED or self.temp_counter >= 420:
                    print("PARKING OCCUPIED AAAAAAAAAAAAAAAAAAAA")
                    self.latest_tracked_vehicle_bbs[license_plate][self.parking_status_key] = ParkingStatus.OCCUPIED

                    # retry to detect vehicle license plate
                    if(self.latest_tracked_vehicle_bbs[license_plate][self.license_detected_key]==self.license_notDetected):

                        # bbs_center_pts = self.calculateCenterOfBbs(license_plate=license_plate, camera_id=camera_id)
                        bottom_midpts = self.calculateBottomOfBbs(vehicle_plate=license_plate, camera_id=camera_id)
                        # bbs_center_pts = self.getBROfBbs(license_plate=license_plate, camera_id=camera_id)
                        # vector_pts = self.getBbVectorToFrameEdge(bottom_midpts[-1], (Constants.default_camera_shape[0], Constants.default_camera_shape[1]))
                        # self.drawVehicleTrail(pts)


                        frame = self.getFrameByCameraId(camera_id)

                        license_bb = self.getLicensePlateBboxUsingModel(parking_space_bb=(self.parking_spaces[j][2][0], self.parking_spaces[j][2][3]),
                                                                        frame=frame,
                                                                        license_detector=license_detector)

                        if (license_bb):
                            # indicate that license plate of the specified vehicle is detected
                            self.latest_tracked_vehicle_bbs[license_plate][self.license_detected_key] = self.license_detected

                            vector_to_license_plate_pts = self.getBbVectorToLicenseCenterToFrame(last_bb_pt=bottom_midpts[-1],
                                                                                          license_bb=license_bb)

                            license_center_pt = IU.GetBoundingBoxCenter(license_bb)

                            vector_to_frame_edge = self.getBbVectorToFrameEdge(last_bb_pt=license_center_pt,
                                                                               frame_dimensions=(Constants.default_camera_shape[0],
                                                                                                 Constants.default_camera_shape[1]))

                            self.drawVehicleTrailUsingVector(bottom_midpts, vector_to_frame_edge)

                            # self.getWindShieldContours(vehicle_bb=bbs[i], frame=frame)

                    break

    def getWindShieldContours(self, vehicle_bb, frame):
        print("vehicle_bb", vehicle_bb, file=sys.stderr)

        # TODO: remove hard-coded vehicle_bb below
        vehicle_bb = [[435,136], [820, 430]]

        vehicle_img = IU.CropImage(img=frame, bounding_set=vehicle_bb)

        # convert to gray
        gray = cv2.cvtColor(vehicle_img, cv2.COLOR_BGR2GRAY)

        # remove noise while maintaining edges
        gray = cv2.bilateralFilter(gray, 11, 17, 17)

        # detect edges
        canny = cv2.Canny(gray, 170, 200)

        # find the contours in canny image
        contours, hierarchy = cv2.findContours(canny.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        # print("HIERARCHY: ", hierarchy, file=sys.stderr)
        # print("CONTOURS", contours, file=sys.stderr)

        # Create copy of original image to draw all contours
        img1 = vehicle_img.copy()
        cv2.drawContours(img1, contours, -1, (0, 255, 0), 3)

        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:30]

        img2 = vehicle_img.copy()
        cv2.drawContours(img2, contours, -1, (0, 255, 0), 3)
        IU.SaveImage(img2, "Top 30 Contours")

    def getLicensePlateBboxUsingModel(self, parking_space_bb, frame, license_detector):
        # returns the license plate bb in respect to the frame
        # parking space bb is in the format [[TL], [BR]]

        # crop parking from frame before detecting license
        parking_space_img = IU.CropImage(frame, (parking_space_bb[0], parking_space_bb[1]))
        IU.SaveImage(parking_space_img, "parking img cropped")

        # TODO: change from parking spot parameter to vehicle bounding box tracked
        status, classes, license_bb, scores = license_detector.DetectObjectsInImage(parking_space_img)

        if status == 0:
            print("ERROR: No license plate was detected.", file=sys.stderr)
            return

        license_bb = license_bb[0]

        # get license plate in respect of original frame, not cropped img that was used for license detection
        rescaled_license_bb = IU.GetChildBBInRespectToNewParent(child_bbox=license_bb,
                                                                 child_parent_bbox_irt_new_parent=parking_space_bb)

        frame = IU.DrawBoundingBoxes(frame, [rescaled_license_bb], color=(0, 255, 0))
        IU.SaveImage(frame, "location of license plate in actual")

        return rescaled_license_bb

    def getBbVectorToLicenseCenterToFrame(self, last_bb_pt, license_bb):
        # get the center of new_bb_pts or for short can just get center of bounding boxes
        center_pt = IU.GetBoundingBoxCenter(license_bb)

        # get Bb vector of last tracked point to the center of license plate
        x1 = last_bb_pt[0]
        y1 = last_bb_pt[1]

        y2 = center_pt[1]

        scaling_factor = y2 / y1
        x2 = x1 * scaling_factor

        return [x2, y2]

    def getLicensePlateBboxUsingContours(self, parking_spot_img):
        # convert to gray
        gray = cv2.cvtColor(parking_spot_img, cv2.COLOR_BGR2GRAY)

        # remove noise while maintaining edges
        gray = cv2.bilateralFilter(gray, 11, 17, 17)

        # detect edges
        canny = cv2.Canny(gray, 170, 200)

        # find the contours in canny image
        contours, hierarchy = cv2.findContours(canny.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        print("HIERARCHY: ",hierarchy)
        print("CONTOURS" ,contours)

        # Create copy of original image to draw all contours
        img1 = parking_spot_img.copy()
        cv2.drawContours(img1, contours, -1, (0, 255, 0), 3)

        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:30]


        img2 = parking_spot_img.copy()
        cv2.drawContours(img2, contours, -1, (0, 255, 0), 3)
        cv2.imshow("5- Top 30 Contours", img2)
        cv2.waitKey(0)

        plate_contour = None
        rectangle_sides = 4

        # loop through the sorted contours and find the rectangle shape
        for c in contours:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.018*peri, True)
            if len(approx) == rectangle_sides:  # Select the contour with 4 corners
                plate_contour = approx  # This is our approx Number Plate Contour

                # Crop those contours and store it in Cropped Images folder
                x, y, w, h = cv2.boundingRect(c)  # This will find out co-ord for plate
                new_img = gray[y:y + h, x:x + w]  # Create new image
                IU.SaveImage(new_img, "contoured_plate")

                break

        # Drawing the selected contour on the original image
        cv2.drawContours(parking_spot_img, [plate_contour], -1, (0, 255, 0), 3)
        IU.SaveImage(parking_spot_img, "final_img_with_contour")

    def getBbVectorToFrameEdge(self, last_bb_pt, frame_dimensions):
        x1 = last_bb_pt[0]
        y1 = last_bb_pt[1]

        y2 = frame_dimensions[1]

        scaling_factor = y2 / y1
        x2 = x1 * scaling_factor

        # if x2 > frame_edge[0]:
        #     x2 = frame_edge[0]

        return [x2, y2]

    def drawVehicleTrailUsingVector(self, vehicle_trail_pts, vector_pt):
        blank_img = self.calculateMinimumVehicleTrail()
        # blank_img = self.base_blank.copy()

        last_vehicle_trail_pt = vehicle_trail_pts[-1]

        # draw lines between each consecutive points
        for i in range(len(vehicle_trail_pts)):
            if i % 2 == 0:
                continue
            pt1 = vehicle_trail_pts[i]
            pt2 = vehicle_trail_pts[i - 1]

            # draw vehicle trail
            print("AAAAAAAAAAAAAAAA VECTOR DRAWN YES", file=sys.stderr)
            blank_img = IU.DrawLine(image=blank_img, point_a=(int(pt1[0]), int(pt1[1])),
                        point_b=(int(pt2[0]), int(pt2[1])), color=(0, 255, 0))

        # draw trail to center
        blank_img = IU.DrawLine(image=blank_img, point_a=(int(last_vehicle_trail_pt[0]), int(last_vehicle_trail_pt[1])),
                                point_b=(int(vector_pt[0]), int(vector_pt[1])), color=(0, 255, 255))

        IU.SaveImage(blank_img, "vector_to_license_center")

    def drawVehicleTrail(self, pts):
        blank_img = self.calculateMinimumVehicleTrail()
        # blank_img = self.base_blank.copy()

        for i in range(len(pts)):
            if i % 2 == 0:
                continue
            pt1 = pts[i]
            pt2 = pts[i - 1]
            blank_img = IU.DrawLine(image=blank_img, point_a=(int(pt1[0]), int(pt1[1])),
                        point_b=(int(pt2[0]), int(pt2[1])), color=(0, 255, 0))

        # perpendicular_pts = self.getPerpendicularPointOnLine(bbs_center_pts)
        # print("BERBENDICULAAAAAAAAAAAAAAR: ", perpendicular_pts)
        # blank_img = self.drawVehicleTrailToBottomParking(blank_img, bbs_center_pts, perpendicular_pts)

        # cv2.imshow("full trail", blank_img)
        IU.SaveImage(blank_img,"vector")
        # cv2.waitKey(0)

    def drawVehicleTrailToBottomParking(self, img, bbs_pts, perpendicular_pts):
        # blank_img = self.base_blank.copy()
        blank_img = img.copy()

        threshold_length = math.ceil(len(bbs_pts) * self.threshold_percentage)

        length = len(bbs_pts)
        perp_length = len(perpendicular_pts)
        # for i in range(len(perpendicular_pts)):
        #     blank_img = IU.DrawLine(image=blank_img, point_a=(int(bbs_pts[i+threshold_length][0]), int(bbs_pts[i+threshold_length][1])),
        #                             point_b=(int(perpendicular_pts[i][0]), int(perpendicular_pts[i][1])), color=(0, 255, 255))

        blank_img = IU.DrawLine(image=blank_img,
                                point_a=(int(bbs_pts[length-1][0]), int(bbs_pts[length-1][1])),
                                point_b=(int(perpendicular_pts[perp_length-1][0]), int(perpendicular_pts[perp_length-1][1])),
                                color=(0, 255, 255))

        blank_img = IU.DrawLine(image=blank_img,
                                point_a=(int(self.parking_spaces[0][2][2][0]), int(self.parking_spaces[0][2][2][1])),
                                point_b=(
                                int(self.parking_spaces[0][2][3][0]), int(self.parking_spaces[0][2][3][1])),
                                color=(0, 255, 255))
        return blank_img

    def getPerpendicularPointOnLine(self, bbs_pts):
        # get [x, y] coordinates of a point on the line perpendicular to specified pts
        perpendicular_pts = []
        parking_BL = self.parking_spaces[0][2][2]
        parking_BR = self.parking_spaces[0][2][3]
        print("BOTTOM LINE PARKING---> (", parking_BL, "," ,parking_BR, ")" )

        threshold_length = math.ceil(len(bbs_pts)*self.threshold_percentage)

        for pt in bbs_pts[threshold_length:]:
            k = ((pt[0]-parking_BL[0])*(parking_BR[0]-pt[0]) + (pt[1]-parking_BL[1])*(parking_BR[1]-parking_BL[1])) \
            / ((parking_BR[0]-parking_BL[0])**2 + (parking_BR[1]-parking_BL[1])**2)

            perpendicular_x = parking_BL[0] + k*(parking_BR[0]-parking_BL[0])
            perpendicular_y = parking_BL[1] + k*(parking_BR[1]-parking_BL[1])

            perpendicular_pts.append([math.ceil(perpendicular_x), math.ceil(perpendicular_y)])

        return perpendicular_pts

    def calculateMinimumVehicleTrail(self):
        blank_img = self.base_blank.copy()

        for j in range(len(self.parking_spaces)):
            parking_bbs = self.parking_spaces[j][2]
            # math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            parking_lane_length_left = math.sqrt((parking_bbs[2][0]-parking_bbs[0][0])**2 + (parking_bbs[2][1]-parking_bbs[0][1])**2)
            parking_lane_length_right = math.sqrt((parking_bbs[3][0]-parking_bbs[1][0])**2 + (parking_bbs[3][1]-parking_bbs[1][1])**2)

            blank_img = IU.DrawLine(image=blank_img, point_a=(int(parking_bbs[2][0]), int(parking_bbs[2][1])),
                                    point_b=(int(parking_bbs[0][0]), int(parking_bbs[0][1])), color=(0, 0, 255))

            blank_img = IU.DrawLine(image=blank_img, point_a=(int(parking_bbs[1][0]), int(parking_bbs[1][1])),
                                    point_b=(int(parking_bbs[3][0]), int(parking_bbs[3][1])), color=(0, 0, 255))

            return blank_img

            # if parking_lane_length_left > parking_lane_length_right:
            #     self.minimum_length_of_vehicle_trail = parking_lane_length_left
            # else:
            #     self.minimum_length_of_vehicle_trail = parking_lane_length_right

    def calculateBottomOfBbs(self, vehicle_plate, camera_id):
        bbs_top_midpoints = []

        # calculate the ceiling midpoints
        for bb in self.latest_tracked_vehicle_bbs[vehicle_plate][self.camera_id_key + str(camera_id)]:
            # calculate BL
            BL = [bb[0][0], bb[1][1]]

            # Apply midpoint formula to get midpoint of top bb
            midpoint = [math.ceil((BL[0]+bb[1][0])/2), math.ceil((BL[1]+bb[1][1])/2)]
            bbs_top_midpoints.append(midpoint)

        return bbs_top_midpoints

    def getBROfBbs(self, vehicle_plate, camera_id):
        bbs_BR_pts = []

        for bb in self.latest_tracked_vehicle_bbs[vehicle_plate][self.camera_id_key + str(camera_id)]:
            bbs_BR_pts.append([bb[1][0], bb[1][1]])

        return bbs_BR_pts

    def calculateCenterOfBbs(self, vehicle_plate, camera_id):
        # returns center pts in format [center_x, center_y]
        bbs_center_pts = []

        # calculate the ceiling center points
        for bb in self.latest_tracked_vehicle_bbs[vehicle_plate][self.camera_id_key+str(camera_id)]:
            # Apply midpoint formula to get center of bb
            center_pt = [math.ceil((bb[0][0]+bb[1][0])/2), math.ceil((bb[0][1]+bb[1][1])/2)]
            print("bb: ", bb)
            print("center: ", center_pt)
            bbs_center_pts.append(center_pt)

        return bbs_center_pts

    def buildVehicleBbHistory(self, bbs, camera_id, vehicle_plate):
        bbs = bbs[0]
        # self.latest_tracked_vehicle_frames[camera_id-self.camera_offset][self.count_latest_tracked_vehicle_frames]=bbs

        # Add new bb of vehicle
        # self.latest_tracked_vehicle_bbs[vehicle_plate].append(bbs)
        self.latest_tracked_vehicle_bbs[vehicle_plate][self.camera_id_key+str(camera_id)].append(bbs)

        # Pop first bb (found at index 1) if bbs stored exceed maximum number of bbs allowed
        # if len(self.latest_tracked_vehicle_bbs[vehicle_plate]) == self.maximum_tracked_vehicle_bbs:
        #     self.latest_tracked_vehicle_bbs[vehicle_plate].pop(1)
            # last_bb = self.latest_tracked_vehicle_bbs[vehicle_plate][self.maximum_tracked_vehicle_bbs-1]
            # second_last_bb = self.latest_tracked_vehicle_bbs[vehicle_plate][self.maximum_tracked_vehicle_bbs-2]
            #
            # if abs(last_bb[0][0]-second_last_bb[0][0]) < 7 and abs(last_bb[0][1]-second_last_bb[0][1]) < 7:
            #     self.should_build_vehicle_bb_history = False
            #     self.calculateCenterOfBbs(vehicle_plate=vehicle_plate)
            # print("popped!")
