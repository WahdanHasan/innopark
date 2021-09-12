import classes.system_utilities.image_utilities.ObjectDetection as OD
import classes.system_utilities.image_utilities.ImageUtilities as IU
import cv2
import time
import numpy as np
from multiprocessing import Process, Pipe
from classes.camera.CameraBuffered import Camera
import ctypes
from classes.enum_classes.Enums import ObjectStatus

class ParkingSpace:
    def __init__(self):
        self.id = -1
        self.bb = []
        self.is_occupied = False

    def UpdateId(self, new_id):
        self.id = new_id

    def UpdateBB(self, new_bb):
        # [TL, TR, BL, BR]
        self.bb = new_bb

    def UpdateStatus(self, is_occupied):
        self.is_occupied = is_occupied


class TrackedObject:
    def __init__(self, object_id, bb):
        self.object_id = object_id
        self.bb = bb

    def StartTracking(self, pipe):

        # frame = pipe.recv()
        #
        # cropped_frame = IU.CropImage(frame, self.bb)
        #
        # old_gray = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)
        #
        # old_pts = cv2.goodFeaturesToTrack(old_gray, 10, 0.01, 10)
        #
        # lk_params = dict(winSize=(100, 100),
        #                  # to avoid aperature problems, make it smaller, but in turn points dont re-allocate correctly
        #                  maxLevel=100,
        #                  criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
        while True:
            # frame = pipe.recv()
            #
            # cropped_frame = IU.CropImage(frame, self.bb)
            #
            # new_gray = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)
            #
            #
            # new_pts, status, err = cv2.calcOpticalFlowPyrLK(old_gray,
            #                                                 new_gray,
            #                                                 old_pts,
            #                                                 None,
            #                                                 **lk_params)
            #
            # avg_x = 0
            # avg_y = 0
            # for i in range(len(new_pts)):
            #     x, y = new_pts[i].ravel()
            #     x_o, y_o = old_pts[i].ravel()
            #     # cv2.circle(cropped_frame, (int(x), int(y)), 3, 255, -1)
            #     avg_x += abs(x - x_o)
            #     avg_y += abs(y - y_o)
            #
            # avg_x = int(avg_x/len(new_pts))
            # avg_y = int(avg_y/len(new_pts))
            #
            # # print(str(avg_x) + " " + str(avg_y))
            #
            # self.bb = [[self.bb[0][0] + avg_x, self.bb[0][1] + avg_y], [self.bb[1][0] + avg_x, self.bb[1][1] + avg_y]]
            #
            # frame = IU.DrawBoundingBoxes(frame, [self.bb])
            frame = pipe.recv()
            pipe.send(self.bb)
            # cv2.imshow("me smoll process frame ", frame)
            # OD.CreateInvertedMask()

            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break




class Tracker:
    import time
    def __init__(self, is_debug_mode):

        self.tracker_process = 0
        self.parking_spaces = []
        self.is_debug_mode = is_debug_mode

    def Start(self, camera_rtsp, camera_id):
        # All parking spots should be instantiated prior to calling this function

        # ADD MASK INITIALIZATION HERE !!!!!!!!!
        self.tracker_process = Process(target=self.Update, args=(camera_rtsp, camera_id))
        self.tracker_process.start()

    def Stop(self):
        # Sets the tracker continue to false then waits for it to stop
        self.tracker_process.terminate()

    # def Update(self, camera_rtsp, camera_id):
    #
    #     parking_space_boxes = []
    #
    #     for i in range(len(self.parking_spaces)):
    #         parking_space_boxes.append(self.parking_spaces[i].bb)
    #
    #     cam_parking = Camera(rtsp_link=camera_rtsp,
    #                          camera_id=camera_id)
    #
    #     start_time = time.time()
    #     seconds_before_display = 1  # displays the frame rate every 1 second
    #     counter = 0
    #
    #     while True:
    #
    #         frame_parking = cam_parking.GetScaledNextFrame()
    #
    #         parking_return_status, parking_classes, parking_bounding_boxes, parking_scores = OD.DetectObjectsInImage(frame_parking)
    #
    #         # if parking_return_status == True:
    #         frame_yolo = IU.DrawBoundingBoxAndClasses(image=frame_parking,
    #                                                   class_names=parking_classes,
    #                                                   probabilities=parking_scores,
    #                                                   bounding_boxes=parking_bounding_boxes)
    #
    #
    #         parking_space_occupied_statuses = []
    #         if len(parking_space_boxes) != 0:
    #             for i in range(len(self.parking_spaces)):
    #                 parking_space_occupied_statuses.append(self.parking_spaces[i].is_occupied)
    #
    #             frame_yolo = IU.DrawParkingBoxes(frame_yolo, parking_space_boxes, parking_space_occupied_statuses)
    #
    #         for i in range(len(self.parking_spaces)):
    #             for j in range(len(parking_bounding_boxes)):
    #                 if OD.IsCarInParkingBBN(self.parking_spaces[i].bb, parking_bounding_boxes[j]):
    #                     cv2.imshow("MASK", OD.CreateInvertedMask(frame_parking, parking_bounding_boxes[j]))
    #                     self.parking_spaces[i].is_occupied = True
    #                 else:
    #                     self.parking_spaces[i].is_occupied = False
    #
    #
    #
    #         cv2.imshow("Camera " + str(camera_id) + " YOLO Detection", frame_yolo)
    #
    #         cv2.imshow("Camera " + str(camera_id) + " view", frame_parking)
    #
    #         counter += 1
    #         if (time.time() - start_time) > seconds_before_display:
    #             print("Camera " + str(camera_id) + " FPS: ", counter / (time.time() - start_time))
    #             counter = 0
    #             start_time = time.time()
    #
    #         if cv2.waitKey(1) & 0xFF == ord('q'):
    #             cv2.destroyAllWindows()
    #             break

    def Update(self, camera_rtsp, camera_id):

        tracked_objects = []
        tracked_object_processes = []
        tracked_object_pipes = []

        # Initialize camera
        cam = Camera(rtsp_link=camera_rtsp,
                     camera_id=camera_id)


        height, width = cam.default_resolution[1], cam.default_resolution[0]

        self.base_mask = np.zeros((height, width, 3), dtype='uint8')
        # self.base_mask = map(tuple, self.base_mask)
        # self.base_mask = tuple(self.base_mask)

        # Debug variables
        start_time = time.time()
        seconds_before_display = 1
        counter = 0


        only_one = False
        # Main loop
        while True:

            frame = cam.GetScaledNextFrame()
            # Detect new entrants
            return_status, detected_ids, detected_bbs = self.DetectNewEntrants(frame)


            if return_status and (not only_one):
                for i in range(len(detected_ids)):
                    conn1, conn2 = Pipe()

                    temp_tracked_object, temp_tracked_object_process = self.CreateNewTrackedObjectProcess(detected_ids[i], detected_bbs[i], conn2)

                    tracked_objects.append(temp_tracked_object)
                    tracked_object_pipes.append(conn1)
                    tracked_object_processes.append(temp_tracked_object_process)

                only_one = True
                print("Detected only one : " + str(return_status))

            for i in range(len(tracked_object_pipes)):
                tracked_object_pipes[i].send(frame)

            for i in range(len(tracked_object_pipes)):
                tracked_object_pipes[i].recv()


            frame_processed = IU.DrawBoundingBoxes(image=frame,
                                                   bounding_boxes=detected_bbs,
                                                   thickness=2)

            # Information code
            if self.is_debug_mode:
                counter += 1
                if (time.time() - start_time) > seconds_before_display:
                    print("Camera " + str(camera_id) + " FPS: ", counter / (time.time() - start_time))
                    counter = 0
                    start_time = time.time()

                cv2.imshow("Camera " + str(camera_id) + " Live Feed", frame)
                cv2.imshow("Camera " + str(camera_id) + " Processed Feed", frame_processed)
                cv2.imshow("Camera " + str(camera_id) + " Mask", self.base_mask)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break

    def UpdateTracker(self, image):  # Work off a camera id or something, don't leave the detection for the user.
        x=10

    def DetectNewEntrants(self, image):
        # Returns new entrants within an image by running YOLO on the image after the application of the base mask
        # This results in only untracked objects being detected

        # masked_image = self.SubtractMaskFromImage(image, self.base_mask)
        masked_image = image.copy()
        return_status, classes, bounding_boxes, _ = OD.DetectObjectsInImage(image=masked_image)


        return return_status, classes, bounding_boxes

    def CreateNewTrackedObjectProcess(self, object_id, bounding_box, pipe):

        temp_tracked_object = TrackedObject(object_id, bounding_box)
        tracked_object_process = Process(target=temp_tracked_object.StartTracking, args=(pipe, ))
        tracked_object_process.start()

        return temp_tracked_object, tracked_object_process

    def AddObjectToTracker(self, name, identifier, bounding_box):
        tracked_object = [name, identifier, bounding_box]

        self.tracked_objects.append(TrackedObject(tracked_object=tracked_object))

    def RemoveObjectFromTracker(self, tracked_object):
        self.tracked_objects.remove(tracked_object)

    def AddParkingSpaceToTracker(self, parking_space_id, parking_space_bb):
        # Add parking space to tracker's list of parking space

        temp_space = ParkingSpace()
        temp_space.UpdateId(parking_space_id)
        temp_space.UpdateBB(parking_space_bb)

        self.parking_spaces.append(temp_space)

    def SubtractMaskFromImage(self, image, mask):
        # Takes an image and subtracts the provided mask from it
        # Returns the outcome of the subtraction

        masked_image = cv2.bitwise_and(image, image, mask=mask)


        return masked_image

    def AddToMask(self, tracked_object):
        # Takes a tracked object and adds its mask to the base mask
        # It should be noted that moving objects should continually remove their old mask and add their own

        if len(tracked_object.bounding_box) == 4:
            bounding_box = IU.GetPartialBoundingBox(bounding_box=tracked_object.bounding_box)
        else:
            bounding_box = tracked_object.bounding_box

        bounding_box_center = IU.GetBoundingBoxCenter(bounding_box=bounding_box)

        self.base_mask = IU.PlaceImage(base_image=self.base_mask,
                                       img_to_place=tracked_object.mask,
                                       center_x=bounding_box_center[0],
                                       center_y=bounding_box_center[1])

    def RemoveFromMask(self, tracked_object): # Change this in the future to not subtract adjacent masks
        # Takes a tracked object and removes its mask from the base mask
        # It should be noted that moving objects should continually remove their old mask and add their own

        if len(tracked_object.bounding_box) == 4:
            bounding_box = IU.GetPartialBoundingBox(bounding_box=tracked_object.bounding_box)
        else:
            bounding_box = tracked_object.bounding_box

        bounding_box_center = IU.GetBoundingBoxCenter(bounding_box=bounding_box)

        tracked_object_mask_height, tracked_object_mask_width, _ = tracked_object.mask.shape

        tracked_object.mask = np.zeros((tracked_object_mask_height, tracked_object_mask_width, 3), dtype='uint8')

        self.base_mask = IU.PlaceImage(base_image=self.base_mask,
                                       img_to_place=tracked_object.mask,
                                       center_x=bounding_box_center[0],
                                       center_y=bounding_box_center[1])

