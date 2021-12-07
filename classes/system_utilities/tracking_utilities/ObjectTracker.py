import sys

import classes.system_utilities.image_utilities.ImageUtilities as IU
import cv2
import time
import numpy as np
from multiprocessing import Process, Pipe, shared_memory
from classes.camera.CameraBuffered import Camera
from classes.system_utilities.tracking_utilities.SubtractionModel import SubtractionModel
from classes.system_utilities.helper_utilities.Enums import EntrantSide, TrackerToTrackedObjectInstruction, TrackedObjectStatus, TrackedObjectToBrokerInstruction, ObjectToPoolManagerInstruction
from classes.system_utilities.helper_utilities import Constants
from classes.super_classes.ShutDownEventListener import ShutDownEventListener

class Tracker(ShutDownEventListener):

    def __init__(self, tracked_object_pool_request_queue, broker_request_queue, detector_request_queue, tracker_initialized_event, detector_initialized_event, shutdown_event, start_system_event, seconds_between_detections=1.5):
        ShutDownEventListener.__init__(self, shutdown_event)
        self.tracker_process = 0
        self.parking_spaces = []
        self.broker_request_queue = broker_request_queue
        self.tracked_object_pool_request_queue = tracked_object_pool_request_queue
        self.detector_request_queue = detector_request_queue
        self.seconds_between_detections = seconds_between_detections
        self.detector_initialized_event = detector_initialized_event
        self.tracker_initialized_event = tracker_initialized_event
        self.shutdown_event = shutdown_event
        self.start_system_event = start_system_event
        self.shared_memory_manager_id = 0
        self.shared_memory_manager_frame = 0
        self.shared_memory_manager_mask = 0
        self.camera_rtsp = 0
        self.camera_id = 0
        self.should_keep_tracking = True
        self.tracker_id = 0

        self.receive_pipe = 0
        self.send_pipe = 0

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

        ShutDownEventListener.initialize(self)

        # Variable declarations
        subtraction_model = SubtractionModel()
        tracked_object_pool_indexes = []
        tracked_object_ids = []
        tracked_object_pipes = []
        tracked_object_bbs_shared_memory_managers = []
        tracked_object_bbs_shared_memory = []
        tracked_object_movement_status = []
        tracked_objects_without_id_prev_bb = []
        tracked_objects_without_id_indexes = []
        self.receive_pipe, self.send_pipe = Pipe()
        time_at_detection = time.time()

        # Initialize camera
        cam = Camera(rtsp_link=self.camera_rtsp,
                     camera_id=self.camera_id)

        # Create shared memory space for frame and mask
        frame = cam.GetScaledNextFrame()
        subtraction_model.FeedSubtractionModel(image=frame, learningRate=0.0001)
        mask = subtraction_model.GetOutput()

        self.shared_memory_manager_frame = shared_memory.SharedMemory(create=True,
                                                                      name=Constants.frame_shared_memory_prefix + str(self.camera_id),
                                                                      size=frame.nbytes)

        self.shared_memory_manager_mask = shared_memory.SharedMemory(create=True,
                                                                     name=Constants.object_tracker_mask_shared_memory_prefix + str(self.camera_id),
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

        self.tracker_initialized_event.set()
        self.detector_initialized_event.wait()
        self.start_system_event.wait()
        # Main loop
        while self.should_keep_tracking:
            if not self.shutdown_should_keep_listening:
                print("[ObjectTracker] Camera " + str(self.camera_id) + "  Cleaning up.", file=sys.stderr)
                self.cleanUp()
                return
            # Write new frame into shared memory space
            frame[:] = cam.GetScaledNextFrame()[:]

            # Feed subtraction model
            subtraction_model.FeedSubtractionModel(image=frame, learningRate=0.0001)

            # Write new mask into shared memory space
            mask[:] = subtraction_model.GetOutput()[:]

            # Send signal to tracked object processes to read frame and mask along with an instruction
            # TODO: Validate for noise on the last and new bounding box if object doesnt have an id. The object can be going the wrong direction as a result.
            for i in range(len(tracked_object_pipes)):
                primary_instruction_to_send = 0
                if tracked_object_movement_status[i] == TrackedObjectStatus.STATIONARY:
                    primary_instruction_to_send = TrackerToTrackedObjectInstruction.OBJECT_STATIONARY
                elif tracked_object_movement_status[i] == TrackedObjectStatus.MOVING:
                    primary_instruction_to_send = TrackerToTrackedObjectInstruction.OBJECT_MOVING

                object_doesnt_have_id = i in tracked_objects_without_id_indexes

                # Get the side from which the object appeared in the camera, then request the broker for information on the entrant
                if object_doesnt_have_id:
                    temp_bb = tracked_object_bbs_shared_memory[i].tolist()
                    if temp_bb == Constants.bb_example:
                        tracked_object_pipes[i].send(primary_instruction_to_send)

                    temp_entrant_side = self.GetEntrantSide(old_bb=tracked_objects_without_id_prev_bb[i],
                                                            new_bb=temp_bb)

                    self.broker_request_queue.put((TrackedObjectToBrokerInstruction.GET_VOYAGER, self.camera_id, temp_entrant_side, self.send_pipe))
                    temp_entrant_id = self.receive_pipe.recv()
                    tracked_object_pipes[i].send([TrackerToTrackedObjectInstruction.STORE_NEW_ID, primary_instruction_to_send, temp_entrant_id])
                    tracked_object_ids[i] = temp_entrant_id
                    tracked_objects_without_id_indexes.pop(i)
                    tracked_objects_without_id_prev_bb.pop(i)
                else:
                    tracked_object_pipes[i].send(primary_instruction_to_send)

            # Check if tracked objects are still within the image
            for i in range(len(tracked_object_pipes)):
                temp_img_bb = IU.GetFullBoundingBox([[0, 0], [width, height]])
                temp_bb = tracked_object_bbs_shared_memory[i].tolist()

                if temp_bb == Constants.bb_example:
                    continue

                temp_are_overlapping = IU.AreBoxesOverlapping(temp_img_bb, temp_bb)

                if temp_are_overlapping < 0.04:
                    try:
                        temp_mask = IU.CropImage(img=mask, bounding_set=temp_bb)

                        white_points_percentage = (np.sum(temp_mask == 255) / (temp_mask.shape[1] * temp_mask.shape[0])) * 100
                    except:
                        white_points_percentage = 50.0

                    if white_points_percentage < 60.0:
                        temp_exit_side = self.GetExitSide(temp_bb, height, width)
                        self.broker_request_queue.put((TrackedObjectToBrokerInstruction.PUT_VOYAGER, self.camera_id, tracked_object_ids[i], temp_exit_side))
                        print("[ObjectTracker] Object exited from " + temp_exit_side.value, file=sys.stderr)
                        self.tracked_object_pool_request_queue.put((ObjectToPoolManagerInstruction.RETURN_PROCESS, tracked_object_pool_indexes[i]))
                        tracked_object_ids.pop(i)
                        tracked_object_bbs_shared_memory.pop(i)
                        tracked_object_bbs_shared_memory_managers.pop(i)
                        tracked_object_movement_status.pop(i)
                        tracked_object_pipes[i].send(TrackerToTrackedObjectInstruction.STOP_TRACKING)
                        tracked_object_pipes.pop(i)
                        tracked_object_pool_indexes.pop(i)


            # Detect new entrants
            if (time.time() - time_at_detection) > self.seconds_between_detections:
                time_at_detection = time.time()
                # print("[Camera " + str(self.camera_id) + "] Ran detector!")
                return_status, detected_classes, detected_bbs = self.DetectNewEntrants(frame, self.send_pipe, self.receive_pipe)

                if return_status and (not only_one):
                    for i in range(len(detected_classes)):

                        # Request for a tracked object to represent the new entrant from the tracked object pool
                        self.tracked_object_pool_request_queue.put((ObjectToPoolManagerInstruction.GET_PROCESS, self.send_pipe))

                        # Receive the tracked object's pipe and its bounding box shared memory manager from the tracked object pool
                        (temp_pipe, temp_shared_memory_bb_manager, temp_process_pool_idx) = self.receive_pipe.recv()

                        # Create an array reference to the tracked object's shared memory bounding box
                        temp_shared_memory_array = np.ndarray(np.asarray(Constants.bb_example, dtype=np.int32).shape, dtype=np.int32, buffer=temp_shared_memory_bb_manager.buf)

                        # Send the tracked object instructions on the object it is supposed to represent
                        temp_pipe.send((self.camera_id, self.tracker_id, detected_bbs[i], self.shared_memory_manager_frame, frame.shape, self.shared_memory_manager_mask, mask.shape))

                        # Add the tracked object pipe and shared memory reference to local arrays
                        tracked_object_pool_indexes.append(temp_process_pool_idx)
                        tracked_object_pipes.append(temp_pipe)
                        tracked_object_bbs_shared_memory_managers.append(temp_shared_memory_bb_manager)
                        tracked_object_bbs_shared_memory.append(temp_shared_memory_array)
                        tracked_object_movement_status.append(TrackedObjectStatus.MOVING)
                        tracked_object_ids.append(None)

                        tracked_objects_without_id_indexes.append(len(tracked_object_pipes) - 1)
                        tracked_objects_without_id_prev_bb.append(detected_bbs[i])

                    # Only create 1 tracked object in total (this is for debugging and while we wait for the tracker to be finished)
                    only_one = True


            # Print fps rate of tracker
            counter += 1
            if (time.time() - start_time) > seconds_before_display:
                print("[ObjectTracker] Camera " + str(self.camera_id) + " FPS: ", counter / (time.time() - start_time))
                counter = 0
                start_time = time.time()

            # cv2.imshow(str(self.camera_id), mask)
            # Quit if user presses 'q', otherwise loop after 1ms
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     cv2.destroyAllWindows()
            #     break

    def StopTracking(self):
        self.should_keep_tracking = False

    def GetExitSide(self, bb, height, width):
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

    def GetEntrantSide(self, old_bb, new_bb):

        # Get BB centers
        old_bb_center = IU.GetBoundingBoxCenter(bounding_box=old_bb)
        new_bb_center = IU.GetBoundingBoxCenter(bounding_box=new_bb)

        # Get object distance traveled horizontally
        dist_horizontal = int(old_bb_center[0] - new_bb_center[0])
        # Get object distance traveled vertically
        dist_vertical = int(old_bb_center[1] - new_bb_center[1])

        # Get greater distance travel side

        # TODO: Get this working
        # if abs(dist_horizontal) > abs(dist_vertical):
        #     if dist_horizontal > 0:
        #         return EntrantSide.LEFT
        #     else:
        #         return EntrantSide.RIGHT
        # else:
        #     if dist_vertical > 0:
        #         return EntrantSide.TOP
        #     else:
        #         return EntrantSide.BOTTOM

        if dist_horizontal > 0:
            return EntrantSide.LEFT
        else:
            return EntrantSide.RIGHT

    def DetectNewEntrants(self, image, send_pipe, receive_pipe):
        # Returns new entrants within an image by running YOLO on the image after the application of the base mask
        # This results in only untracked objects being detected

        # masked_image = self.SubtractMaskFromImage(image, self.base_mask)
        # masked_image = image.copy()
        # send_start_time = time.time()

        self.detector_request_queue.put((self.camera_id, send_pipe))
        # if self.camera_id == 2:
        #     print("SENDING TOOK " + str(time.time() - send_start_time))


        # receive_start_time = time.time()
        return_status, classes, bounding_boxes, _ = receive_pipe.recv()
        # if self.camera_id == 2:
        #     print("RECEIVING TOOK " + str(time.time() - receive_start_time))
        # return_status = True
        # classes = ['CAR']
        # bounding_boxes = [[[511, 245], [720, 388]]]

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

    def cleanUp(self):
        self.receive_pipe.close()
        self.send_pipe.close()
        self.shared_memory_manager_frame.unlink()
        self.shared_memory_manager_mask.unlink()


