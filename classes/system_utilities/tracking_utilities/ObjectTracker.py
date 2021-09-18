import sys

import classes.system_utilities.image_utilities.ObjectDetection as OD
import classes.system_utilities.image_utilities.ImageUtilities as IU
import cv2
import time
import numpy as np
from multiprocessing import Process, Pipe, shared_memory
from classes.camera.CameraBuffered import Camera
from classes.system_utilities.helper_utilities.Enums import EntrantSide
from classes.system_utilities.helper_utilities.Enums import TrackerToTrackedObjectInstruction
from classes.system_utilities.helper_utilities.Enums import TrackedObjectStatus
from classes.system_utilities.helper_utilities.Enums import ParkingStatus
from classes.system_utilities.helper_utilities.Enums import TrackedObjectToBrokerInstruction
from classes.system_utilities.helper_utilities.Enums import ObjectToPoolManagerInstruction

from classes.system_utilities.helper_utilities import Constants


class ParkingSpace:
    def __init__(self):
        self.id = -1
        self.bb = []
        self.status = ParkingStatus.NOT_OCCUPIED.value
        self.occupant_id = -1

    def UpdateId(self, new_id):
        self.id = new_id

    def UpdateBB(self, new_bb):
        # [TL, TR, BL, BR]
        self.bb = new_bb

    def UpdateStatus(self, status):
        self.status = status

    def UpdateOccupant(self, occupant_id):
        self.occupant_id = occupant_id

    def GetId(self):
        return self.id

    def GetBB(self):
        return self.bb

    def GetStatus(self):
        return self.status

    def GetOccupantId(self):
        return self.occupant_id


class Tracker:

    def __init__(self, tracked_object_pool_request_queue, broker_request_queue, is_debug_mode, seconds_between_detections=1):

        self.tracker_process = 0
        self.parking_spaces = []
        self.broker_request_queue = broker_request_queue
        self.is_debug_mode = is_debug_mode
        self.tracked_object_pool_request_queue = tracked_object_pool_request_queue
        self.seconds_between_detections = seconds_between_detections
        self.shared_memory_manager_frame = 0
        self.shared_memory_manager_mask = 0
        self.camera_rtsp = 0
        self.camera_id = 0
        self.should_keep_tracking = True

    def StartProcess(self, camera_rtsp, camera_id):
        # All parking spots should be instantiated prior to calling this function

        print("[ObjectTracker] Starting tracker for camera " + str(camera_id) + ".", file=sys.stderr)
        self.Initialize(camera_rtsp, camera_id)
        self.tracker_process = Process(target=self.StartTracking)
        self.tracker_process.start()

    def StopProcess(self):
        # Sets the tracker continue to false then waits for it to stop
        self.tracker_process.terminate()

    def Initialize(self, camera_rtsp, camera_id):
        self.camera_rtsp = camera_rtsp
        self.camera_id = camera_id

    def StartTracking(self):

        # Variable declarations
        subtraction_model = OD.SubtractionModel()
        tracked_object_ids = []
        tracked_object_pipes = []
        tracked_object_bbs_shared_memory = []
        tracked_object_movement_status = []
        receive_pipe, send_pipe = Pipe()
        time_at_detection = time.time()

        # Initialize camera
        cam = Camera(rtsp_link=self.camera_rtsp,
                     camera_id=self.camera_id)

        # Create shared memory space for frame and mask
        frame = cam.GetScaledNextFrame()
        subtraction_model.FeedSubtractionModel(image=frame, learningRate=0.0001)
        mask = subtraction_model.GetOutput()

        self.shared_memory_manager_frame = shared_memory.SharedMemory(create=True, size=frame.nbytes)
        self.shared_memory_manager_mask = shared_memory.SharedMemory(create=True, size=mask.nbytes)

        frame = np.ndarray(frame.shape, dtype=np.uint8, buffer=self.shared_memory_manager_frame.buf)
        mask = np.ndarray(mask.shape, dtype=np.uint8, buffer=self.shared_memory_manager_mask.buf)

        height, width = cam.default_resolution[1], cam.default_resolution[0]

        self.base_mask = np.zeros((height, width, 3), dtype='uint8')

        # Debug variables
        start_time = time.time()
        seconds_before_display = 1
        counter = 0
        only_one = False

        # Run blank detector to prevent lag on first detection
        return_status, detected_classes, detected_bbs = self.DetectNewEntrants(frame)

        # TODO: Make a new way to get entrant side from the broker, it should be gotten based on the direction the detected object is traveling
        # Main loop
        while self.should_keep_tracking:
            # Write new frame into shared memory space
            frame[:] = cam.GetScaledNextFrame()[:]

            # Feed subtraction model
            subtraction_model.FeedSubtractionModel(image=frame, learningRate=0.0001)

            # Write new mask into shared memory space
            mask[:] = subtraction_model.GetOutput()[:]

            # Send signal to tracked object processes to read frame and mask along with an instruction
            for i in range(len(tracked_object_pipes)):
                if tracked_object_movement_status[i] == TrackedObjectStatus.STATIONARY.value:
                    tracked_object_pipes[i].send(TrackerToTrackedObjectInstruction.OBJECT_STATIONARY)
                elif tracked_object_movement_status[i] == TrackedObjectStatus.MOVING.value:
                    tracked_object_pipes[i].send(TrackerToTrackedObjectInstruction.OBJECT_MOVING)

            # Check if objects are entering/leaving parking spaces and update their status accordingly
            for i in range(len(self.parking_spaces)):
                for j in range(len(tracked_object_bbs_shared_memory)):
                    if self.parking_spaces[i].GetStatus() == ParkingStatus.OCCUPIED.value:
                        # If the parking is occupied and the tracked object isn't the occupant, then continue
                        if self.parking_spaces[i].GetOccupantId() != tracked_object_ids[j]:
                            continue

                    else:
                        # If the parking is not occupied and the tracked object is stationary, then continue
                        if tracked_object_movement_status[j] == TrackedObjectStatus.STATIONARY.value:
                            continue

                    # Hence, if the parking is occupied and the tracked object is the occupant, check if he's still in the parking
                    # Hence, if the parking is not occupied and the object is moving, check if he's in this parking

                    # Check if the tracked object is in the parking
                    is_car_in_parking = OD.IsCarInParkingBBN(self.parking_spaces[i].GetBB(), tracked_object_bbs_shared_memory[j].tolist())

                    # If it is, then update the parking to occupied, else, update it to unoccupied. Update the tracked object accordingly.
                    # TODO: This should be updated to count down how long an object has been in a parking
                    if is_car_in_parking:
                        tracked_object_movement_status[j] = TrackedObjectStatus.STATIONARY.value
                        self.parking_spaces[i].UpdateStatus(status=ParkingStatus.OCCUPIED.value)
                        self.parking_spaces[i].UpdateOccupant(occupant_id=tracked_object_ids[j])
                    else:
                        tracked_object_movement_status[j] = TrackedObjectStatus.MOVING.value
                        self.parking_spaces[i].UpdateStatus(status=ParkingStatus.NOT_OCCUPIED.value)
                        self.parking_spaces[i].UpdateOccupant(occupant_id=-1)










            # Detect new entrants
            if (time.time() - time_at_detection) > self.seconds_between_detections:
                time_at_detection = time.time()
                # print("[Camera " + str(self.camera_id) + "] Ran detector!")
                return_status, detected_classes, detected_bbs = self.DetectNewEntrants(frame)

                if return_status and (not only_one):
                    for i in range(len(detected_classes)):
                        # Get the side from which the object appeared in the camera, then request the broker for information on the entrant
                        entered_object_side = self.GetEntrantSide(detected_bbs[i], height, width)
                        self.broker_request_queue.put((TrackedObjectToBrokerInstruction.GET_VOYAGER, self.camera_id, entered_object_side, send_pipe))
                        entered_object_id = receive_pipe.recv()
                        # Request for a tracked object to represent the new entrant from the tracked object pool
                        self.tracked_object_pool_request_queue.put((ObjectToPoolManagerInstruction.GET_PROCESS, send_pipe))

                        # Receive the tracked object's pipe and its bounding box shared memory manager from the tracked object pool
                        (temp_pipe, temp_shared_memory_bb) = receive_pipe.recv()

                        # Create an array reference to the tracked object's shared memory bounding box
                        temp_shared_memory_array = np.ndarray(np.asarray(Constants.bb_example, dtype=np.int32).shape, dtype=np.int32, buffer=temp_shared_memory_bb.buf)
                        # TODO: Generate random id if the id is "none"

                        # Send the tracked object instructions on the object it is supposed to represent
                        temp_pipe.send((detected_bbs[i], entered_object_id, self.shared_memory_manager_frame, frame.shape, self.shared_memory_manager_mask, mask.shape))

                        # Add the tracked object pipe and shared memory reference to local arrays
                        tracked_object_pipes.append(temp_pipe)
                        tracked_object_bbs_shared_memory.append(temp_shared_memory_array)
                        tracked_object_movement_status.append(TrackedObjectStatus.MOVING.value)
                        tracked_object_ids.append(entered_object_id)

                    # Only create 1 tracked object in total (this is for debugging and while we wait for the tracker to be finished)
                    only_one = True

            # Information code
            if self.is_debug_mode:
                # Print fps rate of tracker
                counter += 1
                if (time.time() - start_time) > seconds_before_display:
                    print("[Camera " + str(self.camera_id) + "] FPS: ", counter / (time.time() - start_time))
                    counter = 0
                    start_time = time.time()

                # Draw parking space boxes
                temp_parking_boxes = []
                temp_parking_box_statuses = []
                for i in range(len(self.parking_spaces)):
                    temp_parking_boxes.append(self.parking_spaces[i].GetBB())
                    temp_parking_box_statuses.append(self.parking_spaces[i].GetStatus())

                frame_processed = IU.DrawParkingBoxes(image=frame,
                                                      bounding_boxes=temp_parking_boxes,
                                                      are_occupied=temp_parking_box_statuses)

                # Draw tracked object boxes
                temp_tracked_boxes = []
                for i in range(len(tracked_object_bbs_shared_memory)):
                    temp_tracked_boxes.append(tracked_object_bbs_shared_memory[i].tolist())

                # frame_processed = IU.DrawBoundingBoxes(image=frame_processed,
                #                                        bounding_boxes=temp_tracked_boxes)

                frame_processed = IU.DrawBoundingBoxAndClasses(image=frame_processed,
                                                               class_names=tracked_object_ids,
                                                               bounding_boxes=temp_tracked_boxes)

                # Show frames
                cv2.imshow("Camera " + str(self.camera_id) + " Live Feed", frame)
                cv2.imshow("Camera " + str(self.camera_id) + " Processed Feed", frame_processed)
                # cv2.imshow("Camera " + str(self.camera_id) + " Mask", self.base_mask)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break

    def StopTracking(self):
        self.should_keep_tracking = False

    def GetEntrantSide(self, bb, height, width):
        # Takes the bounding box of the entrant and the height and width of the image
        # Calculates the side where the entrant came from depending on the distance of the bb center from the center
        # of each side
        # Returns the side as a string

        bb_center = np.array(IU.GetBoundingBoxCenter(bb))

        left_side_point = np.array((0, int(height/2)))
        right_side_point = np.array((width, int(height/2)))
        top_side_point = np.array((int(width/2), 0))
        bottom_side_point = np.array((int(width/2), height))

        # UP DOWN LEFT RIGHT
        sides = (top_side_point, bottom_side_point, left_side_point, right_side_point)
        sides_string = (EntrantSide.TOP, EntrantSide.BOTTOM, EntrantSide.LEFT, EntrantSide.RIGHT)

        side_distances = []

        for i in range(len(sides)):
            side_distances.append(np.linalg.norm(abs(bb_center - sides[i])))

        index_of_closest = 0

        for i in range(len(sides)):
            if side_distances[i] < side_distances[index_of_closest]:
                index_of_closest = i

        print("[Camera " + str(self.camera_id) + "] Detected entrant from the " + sides_string[index_of_closest].value + " side.")
        return sides_string[index_of_closest]

    def DetectNewEntrants(self, image):
        # Returns new entrants within an image by running YOLO on the image after the application of the base mask
        # This results in only untracked objects being detected

        masked_image = self.SubtractMaskFromImage(image, self.base_mask)
        masked_image = image.copy()
        return_status, classes, bounding_boxes, _ = OD.DetectObjectsInImage(image=masked_image)


        return return_status, classes, bounding_boxes

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

        # masked_image = cv2.bitwise_and(image, image, mask=mask)
        masked_image = cv2.subtract(image, mask)

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

