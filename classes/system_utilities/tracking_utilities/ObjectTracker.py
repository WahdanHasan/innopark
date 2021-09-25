import sys

import classes.system_utilities.image_utilities.ImageUtilities as IU
# import classes.system_utilities.image_utilities.ObjectDetection as OD
import cv2
import time
import numpy as np
from multiprocessing import Process, Pipe, shared_memory
from classes.camera.CameraBuffered import Camera
from classes.system_utilities.tracking_utilities.SubtractionModel import SubtractionModel
from classes.system_utilities.helper_utilities.Enums import EntrantSide, TrackerToTrackedObjectInstruction, TrackedObjectStatus, TrackedObjectToBrokerInstruction, ObjectToPoolManagerInstruction
from classes.system_utilities.helper_utilities import Constants

class Tracker:

    def __init__(self, tracked_object_pool_request_queue, broker_request_queue, detector_request_queue, detector_initialized_event, seconds_between_detections=1):

        self.tracker_process = 0
        self.parking_spaces = []
        self.broker_request_queue = broker_request_queue
        self.tracked_object_pool_request_queue = tracked_object_pool_request_queue
        self.detector_request_queue = detector_request_queue
        self.seconds_between_detections = seconds_between_detections
        self.detector_initialized_event = detector_initialized_event
        self.shared_memory_manager_id = 0
        self.shared_memory_manager_frame = 0
        self.shared_memory_manager_mask = 0
        self.camera_rtsp = 0
        self.camera_id = 0
        self.should_keep_tracking = True
        self.tracker_id = 0

    def StartProcess(self, tracker_id, camera_rtsp, camera_id):
        # All parking spots should be instantiated prior to calling this function

        print("[ObjectTracker] Starting tracker for camera " + str(camera_id) + ".", file=sys.stderr)
        self.Initialize(tracker_id, camera_rtsp, camera_id)
        self.tracker_process = Process(target=self.StartTracking)
        self.tracker_process.start()

    def StopProcess(self):
        # Sets the tracker continue to false then waits for it to stop
        self.tracker_process.terminate()

    def Initialize(self, tracker_id, camera_rtsp, camera_id):

        self.tracker_id = tracker_id

        self.camera_rtsp = camera_rtsp
        self.camera_id = camera_id

    def StartTracking(self):

        # Variable declarations
        subtraction_model = SubtractionModel()
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

        self.shared_memory_manager_frame = shared_memory.SharedMemory(create=True,
                                                                      name=Constants.object_tracker_frame_shared_memory_prefix + str(self.tracker_id),
                                                                      size=frame.nbytes)

        self.shared_memory_manager_mask = shared_memory.SharedMemory(create=True,
                                                                     name=Constants.object_tracker_mask_shared_memory_prefix + str(self.tracker_id),
                                                                     size=mask.nbytes)

        frame = np.ndarray(frame.shape, dtype=np.uint8, buffer=self.shared_memory_manager_frame.buf)
        mask = np.ndarray(mask.shape, dtype=np.uint8, buffer=self.shared_memory_manager_mask.buf)

        height, width = cam.default_resolution[1], cam.default_resolution[0]

        self.base_mask = np.zeros((height, width, 3), dtype='uint8')

        # Debug variables
        start_time = time.time()
        seconds_before_display = 1
        counter = 0
        only_one = False
        return_status = False

        # Run blank detector to prevent lag on first detection
        self.detector_initialized_event.wait()

        # return_status, detected_classes, detected_bbs = self.DetectNewEntrants(frame, send_pipe, receive_pipe)

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








            # Detect new entrants
            if (time.time() - time_at_detection) > self.seconds_between_detections:
                time_at_detection = time.time()
                # print("[Camera " + str(self.camera_id) + "] Ran detector!")
                return_status, detected_classes, detected_bbs = self.DetectNewEntrants(frame, send_pipe, receive_pipe)

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
                        temp_pipe.send((self.camera_id, self.tracker_id, detected_bbs[i], entered_object_id, self.shared_memory_manager_frame, frame.shape, self.shared_memory_manager_mask, mask.shape))

                        # Add the tracked object pipe and shared memory reference to local arrays
                        tracked_object_pipes.append(temp_pipe)
                        tracked_object_bbs_shared_memory.append(temp_shared_memory_array)
                        tracked_object_movement_status.append(TrackedObjectStatus.MOVING.value)
                        tracked_object_ids.append(entered_object_id)

                    # Only create 1 tracked object in total (this is for debugging and while we wait for the tracker to be finished)
                    only_one = True


            # Print fps rate of tracker
            counter += 1
            if (time.time() - start_time) > seconds_before_display:
                print("[ObjectTracker] Camera " + str(self.camera_id) + " FPS: ", counter / (time.time() - start_time))
                counter = 0
                start_time = time.time()

            # temp_frame = frame.copy()
            # if only_one:
            #     # Draw tracked object boxes
            #     temp_tracked_boxes = []
            #     for i in range(len(tracked_object_bbs_shared_memory)):
            #         temp_tracked_boxes.append(tracked_object_bbs_shared_memory[i].tolist())
            #
            #
            #
            #     temp_frame = IU.DrawBoundingBoxAndClasses(image=frame,
            #                                               class_names=tracked_object_ids,
            #                                               bounding_boxes=temp_tracked_boxes)

            # cv2.imshow("Camera " + str(self.camera_id), temp_frame)

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

    def DetectNewEntrants(self, image, send_pipe, receive_pipe):
        # Returns new entrants within an image by running YOLO on the image after the application of the base mask
        # This results in only untracked objects being detected

        masked_image = self.SubtractMaskFromImage(image, self.base_mask)
        masked_image = image.copy()
        self.detector_request_queue.put((self.tracker_id, send_pipe))
        return_status, classes, bounding_boxes, _ = receive_pipe.recv()
        # return_status, classes, bounding_boxes, _ = OD.DetectObjectsInImage(image=masked_image)

        return return_status, classes, bounding_boxes

    def RemoveObjectFromTracker(self, tracked_object):
        self.tracked_objects.remove(tracked_object)

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

