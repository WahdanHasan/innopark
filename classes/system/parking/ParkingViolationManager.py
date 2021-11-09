from classes.super_classes.TrackedObjectListener import TrackedObjectListener
from classes.system.parking.ParkingSpace import ParkingSpace
from classes.system_utilities.helper_utilities import Constants
from classes.system_utilities.helper_utilities.Enums import ParkingStatus
from classes.system_utilities.image_utilities import ImageUtilities as IU
from classes.system_utilities.data_utilities.Avenues import GetAllParkings
from classes.system_utilities.helper_utilities.Enums import ImageResolution

from multiprocessing import Process, shared_memory
import numpy as np
import cv2
import sys
import json
import time
import math



class ParkingViolationManager(TrackedObjectListener):

    def __init__(self, amount_of_trackers, new_object_in_pool_event, shutdown_event, start_system_event):

        super().__init__(amount_of_trackers, new_object_in_pool_event)
        self.shutdown_event = shutdown_event
        self.start_system_event = start_system_event
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

        self.minimum_length_of_vehicle_trail = 0

        # self.maximum_tracked_vehicle_bbs = 100

        self.camera_offset = len(Constants.ENTRANCE_CAMERA_DETAILS)

        self.latest_tracked_vehicle_bbs = {}
        self.should_build_vehicle_bb_history = True

        # for i in range(len(Constants.CAMERA_DETAILS)):
        #     self.latest_tracked_vehicle_frames.append([None]*self.maximum_tracked_vehicle_frame_history)

        self.is_debug_mode = True
        self.frame_shms = []
        self.frames = []

        self.temp_counter = 0
        self.threshold_percentage = 0.75

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
        self.tariff_manager_process.terminate()

    def startManaging(self):
        super().initialize()
        self.createSharedMemoryStuff(self.amount_of_trackers)

        self.start_system_event.wait()

        while self.should_keep_managing:

            ids, bbs = self.getAllActiveTrackedProcessItems()

            self.checkAndUpdateViolationStatuses(ids=ids,
                                                bbs=bbs)

            # if self.is_debug_mode:
            #     self.writeDebugItems()

            time.sleep(0.033)

    def checkAndUpdateViolationStatuses(self, ids, bbs):
        # An object tracker cannot be on the id 0
        if not ids or ids is None:
            return

        if not bbs or bbs is None:
            return

        for i in range(len(bbs)):
            self.temp_counter +=1
            vehicle_plate = ids[2][i]
            camera_id = ids[1][i]

            # Initialize vehicle_plate dict for new vehicle
            if vehicle_plate not in self.latest_tracked_vehicle_bbs:
                # initialize the parking status
                self.latest_tracked_vehicle_bbs[vehicle_plate] = {
                    self.parking_status_key:ParkingStatus.NOT_OCCUPIED
                }

                # initialize a list for each camera
                for camera_details in Constants.CAMERA_DETAILS:
                    self.latest_tracked_vehicle_bbs[vehicle_plate][self.camera_id_key+str(camera_details[0])] = []

            # Build the history of vehicle bbs if vehicle is not parked
            if self.latest_tracked_vehicle_bbs[vehicle_plate][self.parking_status_key] == ParkingStatus.NOT_OCCUPIED:
                self.buildVehicleBbHistory(bbs=bbs, camera_id=camera_id, vehicle_plate=vehicle_plate)

            for j in range(len(self.parking_spaces)):
                # if camera_id != self.parking_spaces[j].camera_id:
                if camera_id != self.parking_spaces[j][0]:
                    continue

                # if self.parking_spaces.status == ParkingStatus.OCCUPIED:
                if self.parking_spaces[j][3] == ParkingStatus.OCCUPIED or self.temp_counter == 200:
                    print("PARKING OCCUPIED AAAAAAAAAAAAAAAAAAAA")
                    self.latest_tracked_vehicle_bbs[vehicle_plate][self.parking_status_key] = ParkingStatus.OCCUPIED
                    # bbs_center_pts = self.calculateCenterOfBbs(vehicle_plate=vehicle_plate, camera_id=camera_id)
                    bottom_midpts = self.calculateBottomOfBbs(vehicle_plate=vehicle_plate, camera_id=camera_id)
                    # bbs_center_pts = self.getBROfBbs(vehicle_plate=vehicle_plate, camera_id=camera_id)
                    vector_pts = self.getBbVectorToFrameEdge(bottom_midpts[-1], Constants.default_camera_shape[1])
                    # self.drawVehicleTrail(pts)
                    self.drawVehicleTrailUsingVector(bottom_midpts, vector_pts)
                    break

    def getBbVectorToFrameEdge(self, last_bb_pt, frame_edge_y):
        x1 = last_bb_pt[0]
        y1 = last_bb_pt[1]

        x2 = 0
        y2 = frame_edge_y

        scaling_factor = y2 / y1
        x2 = x1 * scaling_factor

        return [x2, y2]


    def drawVehicleTrailUsingVector(self, bbs_pts, vector_pt):
        blank_img = self.calculateMinimumVehicleTrail()
        # blank_img = self.base_blank.copy()

        last_bb_pt = bbs_pts[-1]

        for i in range(len(bbs_pts)):
            if i % 2 == 0:
                continue
            pt1 = bbs_pts[i]
            pt2 = bbs_pts[i - 1]
            print("center pt: (", pt1, pt2, ")")
            blank_img = IU.DrawLine(image=blank_img, point_a=(int(pt1[0]), int(pt1[1])) ,
                        point_b=(int(pt2[0]), int(pt2[1])), color=(0, 255, 0))

        blank_img = IU.DrawLine(image=blank_img, point_a=(int(last_bb_pt[0]), int(last_bb_pt[1])),
                                point_b=(int(vector_pt[0]), int(vector_pt[1])), color=(0, 255, 255))

        blank_img = cv2.circle(blank_img, ((int(vector_pt[0])), int(vector_pt[1])), 100, (255, 255, 0), -1)

        IU.SaveImage(blank_img, "vector_3")

    def drawVehicleTrail(self, pts):
        blank_img = self.calculateMinimumVehicleTrail()
        # blank_img = self.base_blank.copy()

        # format of bbs_center_pt is [center_x, center_y]
        for i in range(len(pts)):
            if i % 2 == 0:
                continue
            pt1 = pts[i]
            pt2 = pts[i - 1]
            print("center pt: (", pt1, pt2, ")")
            blank_img = IU.DrawLine(image=blank_img, point_a=(int(pt1[0]), int(pt1[1])) ,
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
            print("bb: ", bb)
            print("center: ", midpoint)
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
